from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import json
import pandas as pd
import re
import requests
from .models import UploadedFile

# Hugging Face API setup
HF_API_TOKEN = "dummy get a token from Huggingface"
HF_API_URL = "https://router.huggingface.co/nebius/v1/chat/completions"

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES['file']
        
        # Save file
        filename = default_storage.save(f'uploads/{file.name}', file)
        file_path = default_storage.path(filename)
        
        # Save to DB
        uploaded_file = UploadedFile.objects.create(
            filename=file.name,
            file_path=file_path
        )
        
        return JsonResponse({
            'success': True,
            'file_id': uploaded_file.id,
            'filename': file.name
        })

@csrf_exempt
def preview_file(request, file_id):
    if request.method == 'GET':
        file_obj = UploadedFile.objects.get(id=file_id)
        
        # Read file
        if file_obj.filename.endswith('.csv'):
            df = pd.read_csv(file_obj.file_path)
        else:
            df = pd.read_excel(file_obj.file_path)
        
        # Get text columns
        text_columns = [col for col in df.columns if df[col].dtype == 'object']
        
        return JsonResponse({
            'success': True,
            'preview_data': df.head().to_dict('records'),
            'columns': list(df.columns),
            'text_columns': text_columns,
            'total_rows': len(df)
        })

def extract_column_pattern_replacement(text, available_columns=None):
    """
    Extract target column, regex pattern, and replacement value from natural language
    
    Args:
        text (str): Natural language description
        available_columns (list): List of available column names in the dataset
    
    Returns:
        tuple: (target_column, regex_pattern, replacement_value)
    """
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Include available columns in context
    column_context = ""
    if available_columns:
        column_context = f"\nAvailable columns in the dataset: {', '.join(available_columns)}"
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a data processing assistant. Always respond in the exact format: TARGET_COLUMN|||REGEX_PATTERN|||REPLACEMENT_VALUE"
            },
            {
                "role": "user",
                "content": f"""Analyze this data processing request: "{text}"{column_context}

CRITICAL: Return ONLY in this format: TARGET_COLUMN|||REGEX_PATTERN|||REPLACEMENT_VALUE

Examples:
- "Replace the Name column with REDACTED" → Name|||\\b[A-Za-z]+(?:\\s[A-Za-z]+)*\\b|||REDACTED
- "Find emails in Email column and replace with HIDDEN" → Email|||\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{{2,}}\\b|||HIDDEN  
- "Replace phone numbers in Contact column with [PHONE]" → Contact|||\\b\\d{{3}}-\\d{{3}}-\\d{{4}}\\b|||[PHONE]
- "Mask all values in Name column with RHOMBUS" → Name|||.*|||RHOMBUS
- "Find credit cards in Payment column" → Payment|||\\b\\d{{4}}[\\s-]?\\d{{4}}[\\s-]?\\d{{4}}[\\s-]?\\d{{4}}\\b|||[CARD]

Rules:
1. Identify the target column from the user's description
2. Generate regex that matches VALUES in that column (not the column name)
3. Use the replacement value specified by user, or create appropriate placeholder
4. Use double backslashes for escaping
5. Use {{}} for quantifiers in regex
6. If user wants to replace ALL values in a column, use .* or .+ pattern

Your response (format: column|||pattern|||replacement):"""
            }
        ],
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-fast",
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {result}")
            
            # Handle different response formats
            content = None
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"].strip()
            elif isinstance(result, list) and len(result) > 0:
                content = result[0].get("generated_text", "").strip()
            elif "generated_text" in result:
                content = result["generated_text"].strip()
            
            if content:
                print(f"LLM Response: {content}")
                
                # Clean response
                content = content.replace('```', '').replace('`', '').strip()
                
                # Parse the three-part response
                if content.count("|||") == 2:
                    parts = content.split("|||")
                    if len(parts) == 3:
                        target_column = parts[0].strip()
                        regex_pattern = parts[1].strip()
                        replacement_value = parts[2].strip()
                        
                        # Validate regex pattern
                        try:
                            re.compile(regex_pattern)
                            
                            # Validate column name if available_columns provided
                            if available_columns and target_column not in available_columns:
                                # Try to find closest match
                                target_column = find_closest_column(target_column, available_columns)
                            
                            print(f"✓ Extracted: Column='{target_column}', Pattern='{regex_pattern}', Replacement='{replacement_value}'")
                            return target_column, regex_pattern, replacement_value
                            
                        except re.error as e:
                            print(f"Invalid regex generated: {regex_pattern}, Error: {e}")
        
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error calling LLM: {e}")
    
    # Fallback parsing if LLM fails
    return parse_fallback(text, available_columns)

def find_closest_column(target, available_columns):
    """Find the closest matching column name"""
    if not available_columns:
        return target
        
    target_lower = target.lower()
    
    # Exact match (case insensitive)
    for col in available_columns:
        if col.lower() == target_lower:
            return col
    
    # Partial match
    for col in available_columns:
        if target_lower in col.lower() or col.lower() in target_lower:
            return col
    
    # Return first available column as last resort
    return available_columns[0]

def parse_fallback(text, available_columns):
    """
    Fallback parsing when LLM fails to return proper format
    """
    text_lower = text.lower()
    
    # Extract target column
    target_column = None
    if available_columns:
        for col in available_columns:
            if col.lower() in text_lower:
                target_column = col
                break
    
    if not target_column:
        # Try to extract from common patterns
        column_keywords = ['name', 'email', 'phone', 'contact', 'address', 'id']
        for keyword in column_keywords:
            if keyword in text_lower:
                if available_columns:
                    # Find matching column
                    for col in available_columns:
                        if keyword in col.lower():
                            target_column = col
                            break
                if not target_column:
                    target_column = keyword.title()
                break
    
    # Extract replacement value
    replacement_value = "REDACTED"  # default
    if "with" in text_lower:
        # Try to extract what comes after "with"
        parts = text.split("with")
        if len(parts) > 1:
            potential_replacement = parts[1].strip().strip('"\'')
            if potential_replacement:
                replacement_value = potential_replacement
    
    # Generate appropriate regex pattern
    regex_pattern = get_pattern_for_column(target_column, text_lower)
    
    return target_column or (available_columns[0] if available_columns else "Name"), regex_pattern, replacement_value

def get_pattern_for_column(column_name, description):
    """Generate appropriate regex pattern based on column name and description"""
    if not column_name:
        return r'\b\w+\b'
    
    column_lower = column_name.lower()
    
    # Check if user wants to replace ALL values in column
    if "replace" in description and "column" in description and "with" in description:
        return r'.*'  # Match everything
    
    patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'name': r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b',
        'id': r'\b\d+\b',
        'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)\b',
        'zip': r'\b\d{5}(?:-\d{4})?\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'url': r'https?://[^\s]+',
        'date': r'\b\d{1,2}/\d{1,2}/\d{4}\b'
    }
    
    # Check for pattern keywords in column name
    for keyword, pattern in patterns.items():
        if keyword in column_lower:
            return pattern
    
    # Default pattern for any text
    return r'\b[A-Za-z]+(?:\s[A-Za-z]+)*\b'

def apply_targeted_replacement(df, target_column, regex_pattern, replacement_value):
    """
    Apply regex replacement to a specific column only
    
    Args:
        df: pandas DataFrame
        target_column: Column name to process
        regex_pattern: Regex pattern to match
        replacement_value: Value to replace with
    
    Returns:
        tuple: (modified_df, success_message, matches_found, processed_columns)
    """
    processed_columns = []
    matches_found = 0
    
    if target_column not in df.columns:
        return df, f"Error: Column '{target_column}' not found in data", 0, []
    
    try:
        # Convert to string and apply replacement only to target column
        original_series = df[target_column].astype(str)
        modified_series = original_series.str.replace(regex_pattern, replacement_value, regex=True)
        
        # Count matches
        matches_found = sum(1 for orig, mod in zip(original_series, modified_series) if orig != mod)
        
        if matches_found > 0:
            df[target_column] = modified_series
            processed_columns.append(target_column)
            message = f"✓ Successfully processed column '{target_column}': {matches_found} replacements made"
        else:
            message = f"⚠ No matches found in column '{target_column}' with pattern '{regex_pattern}'"
        
        return df, message, matches_found, processed_columns
        
    except Exception as e:
        return df, f"Error processing column '{target_column}': {str(e)}", 0, []

# Keep the old function for backwards compatibility
def find_matching_columns(df, regex_pattern):
    """Find columns that contain the pattern (legacy function)"""
    matching_columns = []
    
    for column in df.columns:
        if df[column].dtype == 'object':  # Only text columns
            # Check if pattern exists in this column
            sample_data = df[column].head(20).fillna('').astype(str)
            try:
                if sample_data.str.contains(regex_pattern, regex=True, na=False).any():
                    matching_columns.append(column)
            except re.error:
                # If regex is invalid, skip this column
                continue
    
    return matching_columns

@csrf_exempt
def process_file(request, file_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        natural_language_input = data['text']  # e.g., "Replace the Name column with RHOMBUS"
        
        # Get file using file_id from URL
        file_obj = UploadedFile.objects.get(id=file_id)
        
        # Read file
        if file_obj.filename.endswith('.csv'):
            df = pd.read_csv(file_obj.file_path)
        else:
            df = pd.read_excel(file_obj.file_path)
        
        # Get available columns for context
        available_columns = list(df.columns)
        
        # Use NEW LLM function to extract target column, pattern, and replacement
        target_column, regex_pattern, replacement_value = extract_column_pattern_replacement(
            natural_language_input, 
            available_columns
        )
        
        print(f"Target Column: {target_column}")
        print(f"Regex Pattern: {regex_pattern}")
        print(f"Replacement: {replacement_value}")
        
        # Apply replacement to the specific target column only
        df_modified, message, matches_found, processed_columns = apply_targeted_replacement(
            df, target_column, regex_pattern, replacement_value
        )
        
        # Save the modified file back (overwriting original)
        if file_obj.filename.endswith('.csv'):
            df_modified.to_csv(file_obj.file_path, index=False)
        else:
            df_modified.to_excel(file_obj.file_path, index=False)
        
        return JsonResponse({
            'success': True,
            'input_text': natural_language_input,
            'target_column': target_column,
            'regex_pattern': regex_pattern,
            'replacement_value': replacement_value,
            'columns_processed': processed_columns,
            'matches_found': matches_found,
            'message': message,
            'processed_data': df_modified.head(10).to_dict('records')  # Return first 10 rows as preview
        })


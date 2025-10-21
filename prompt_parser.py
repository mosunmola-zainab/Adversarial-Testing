"""
Prompt Metadata Parser
Extracts numeric and semantic constraints directly from the input prompt
"""

import re

def parse_amount(value: str) -> float:
    """
    Normalizes monetary amount strings to float values.
    Args:
        amount_str (str): The monetary amount string (e.g., "1.5 million", "$2,000").
    Returns:
        float: The normalized monetary amount.
    """
     # Normalize numeric value
    if isinstance(value, (int, float)):  # handle numeric directly
        return float(value)

    if not isinstance(value, str):
        return None
    
    multiplier = 1
    value = value.strip().lower().replace('$', '')

    if 'million' in value:
        multiplier = 1e6
        value = re.sub(r'\s*million', '', value, flags=re.IGNORECASE)
    elif 'billion' in value:
        multiplier = 1e9
        value = re.sub(r'\s*billion', '', value, flags=re.IGNORECASE)
    amount = float(value.replace(',', '').strip()) * multiplier

    return amount

def parse_constraints(prompt: str) -> dict:
    """
    Extract constraints (like numeric limits, word count, timeframes) from the prompt text.
    Args:
        prompt (str): The input prompt containing constraints.
    Returns:
        dict: A dictionary with extracted constraints.
    """
    constraints = {}

    # Detects word count: allow commas, decimals, words or word
    w_match = re.search(
        r"(?:(?:between|from)\s*(?P<w_low>\d{2,4})\s*(?:-|to|and)\s*(?P<w_high>\d{2,4})|(?P<w_target>\d{2,4}))\s*(?:words?|word)",
        prompt, re.IGNORECASE
    )

    if w_match:
        if w_match.group("w_low") and w_match.group("w_high"): # detects range
            lower = int(w_match.group("w_low").replace(",", ""))
            upper = int(w_match.group("w_high").replace(",", ""))
            constraints["word_count"] = {
                "type": "range",
                "lower_bound": lower,
                "upper_bound": upper,
                "target": (lower + upper) // 2,
                "tolerance": (upper - lower) // 2
            }
        else: # detects single value
            value = int(w_match.group(3).replace(",", ""))
            tolerance = max(10, int(round(0.1 * value))) # 10% tolerance or at least 10 words
            constraints["word_count"] = {
                "type": "fixed",
                "lower_bound": value - tolerance,
                "upper_bound": value + tolerance,
                "target": value,
                "tolerance": tolerance
            }
    
    # Budget constraints (max/min/fixed/neutral): accept $ sign, commas, decimals, million/billion
    pattern_budget = re.search(
        r"(?:(?:under|below|maximum of|up to|not exceeding|≤|less than)\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion))|"
        r"(?:at least|minimum of|no less than|exceeding|more than|over|≥)\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion))|"
        r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion))\s*(?:budget|cost|spend|capex|investment)?)",
        prompt, re.IGNORECASE
    )

    if pattern_budget:
        raw_value = pattern_budget.group(1) or pattern_budget.group(2) or pattern_budget.group(3)
        amount = parse_amount(raw_value)
        if pattern_budget.group(1):
            constraint_type = "max"
        elif pattern_budget.group(2):
            constraint_type = "min"
        else:
            constraint_type = "fixed"

        constraints["budget"] = {
            "type": constraint_type,
            "target": amount,
            "upper_bound": amount if constraint_type == "max" else None,
            "lower_bound": amount if constraint_type == "min" else None,
            "raw_value": raw_value
        }

    # Percentage constraints (fixed or range): accepts decimals and percent sign and word
    pattern_percent = re.search(
        r"(?:(?:between|from)\s*(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)?\s*(?:-|to|and)\s*(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)?|"
        r"(\d{1,3}(?:\.\d+)?)\s*(?:percent|%))",
        prompt, re.IGNORECASE
    )
    if pattern_percent:
        if pattern_percent.group(1) and pattern_percent.group(2): # range
            lower = float(pattern_percent.group(1))
            upper = float(pattern_percent.group(2))
            constraints["percentage"] = {
                "type": "range",
                "lower_bound": lower,
                "upper_bound": upper,
                "target": (lower + upper) / 2.0,
                "tolerance": (upper - lower) / 2.0
            }
        else: # fixed percentage
            raw_value = float(pattern_percent.group(3))
            tolerance = max(1.0, round(0.1 * raw_value, 2)) # 10% tolerance or at least 1%
            constraints["percentage"] = {
                "type": "fixed",
                "target": raw_value,
                "lower_bound": raw_value - tolerance,
                "upper_bound": raw_value + tolerance,
                "tolerance": tolerance
            }
    
    # Timeframe constraints (fixed or range): accepts days, weeks, months, years, abbreviations and ranges
    pattern_time = re.search(
        r"(?:(?:between|from)\s*(\d{1,4})\s*(days?|weeks?|months?|years?)\s*(?:-|to|and)\s*(\d{1,4})\s*(days?|weeks?|months?|years?)|"
        r"(\d{1,4})\s*(days?|weeks?|months?|years?))",
        prompt, re.IGNORECASE
    )

    if pattern_time:
        if pattern_time.group(1) and pattern_time.group(3): # range
            lower = int(pattern_time.group(1))
            upper = int(pattern_time.group(3))
            unit = pattern_time.group(2) 
            constraints["timeframe"] = {
                "type": "range",
                "unit": unit,
                "lower_bound": lower,
                "upper_bound": upper,
                "target": (lower + upper) // 2,
            }
        
        else: # fixed timeframe
            value = int(pattern_time.group(5) or 0)
            unit = pattern_time.group(6)
            constraints["timeframe"] = {
                "type": "fixed",
                "unit": unit,
                "target": value,
            }
        
    return constraints


prompt = """
Today is Oct 10, 2025. Write exactly 150 words.
Capex must not exceed $30 billion over 5 years.
Target EV share between 45% and 55% by 2030.
Pilot runs for 90 days.
"""

print(parse_constraints(prompt))

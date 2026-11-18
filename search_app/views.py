from pathlib import Path
import sys
import csv
import difflib
import os
from django.conf import settings
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
  sys.path.insert(0, str(BASE_DIR))

from project import web_search

def index(request: HttpRequest):
    return render(request, 'search_app/index.html')

# read and map the current wips.csv file to get a lookup of who has each design of those that are currently in progress. This is used to display the "Who has it" field in the search results.
# open the fire read only if it exists, otherwise return an empty lookup
# for each non blank row, map the design name (lowercase, stripped of whitespace) to the "Who Has" value (stripped of whitespace)
# To get the clean row, we will strip whitespace from the keys and values, and convert the keys to lowercase. We will also ignore any rows that have a blank design name or a blank "Who Has" value.
# ignore any rows that have a blank design name or a blank "Who Has" value.
# ignore unused columns, and only use the "Design" and "Who Has" columns. The CSV file may have other columns that we don't care about, so we will ignore them.
# assign the result to a dictionary where the key is the design name and the value is the "Who Has" value. The design name will be converted to lowercase and stripped of whitespace, and the "Who Has" value will be stripped of whitespace.
# Finally return the lookup dictionary containing the mapping of design names to "Who Has" values. If the file does not exist, return an empty dictionary.

def get_stitcher_lookup():
    """Reads 'current wips.csv' and maps 'Design' -> 'Who Has'."""
    lookup: dict[str, str] = {}
    # Get the path to the CSV file in the search_app directory
    file_path = os.path.join(settings.BASE_DIR, 'search_app', 'current wips.csv')

    if os.path.exists(file_path):
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                clean_row = {k.strip().lower(): (v or '').strip() for k, v in row.items() if k}
                design_name = " ".join(clean_row.get('design', '').lower().split())
                who_has = clean_row.get('who has', '')
                
                if design_name and who_has:
                    lookup[design_name] = who_has
    return lookup

# First make sure the project name is a string, otherwise return an empty string. Then clean the project name by converting it to lowercase and stripping whitespace. Check for an exact match in the lookup dictionary first. If found, return the corresponding "Who Has" value. If not found, use difflib.get_close_matches to find a close match with a cutoff of 0.90. If a close match is found, return the corresponding "Who Has" value. If no matches are found, return an empty string.
# convert the project name to lowercase and strip whitespace before checking for matches in the lookup dictionary. This ensures that the search is case-insensitive and ignores leading/trailing whitespace. The function will return the "Who Has" value for the exact match or close match, or an empty string if no match is found.
# if the project name is in the lookup dictionary, return the corresponding "Who Has" value. If not, use difflib.get_close_matches to find a close match with a cutoff of 0.90. If a close match is found, return the corresponding "Who Has" value. If no matches are found, return an empty string.
# if no exact match is found, use difflib.get_close_matches to find a close match with a cutoff of 0.90. If a close match is found, return the corresponding "Who Has" value. If no matches are found, return an empty string.
# if no matches are found, return an empty string. This ensures that the function always returns a string, either the "Who Has" value or an empty string if no match is found.

def find_stitcher(project_name: str | bool | None, lookup: dict[str, str]) -> str:
    """Checks for an exact match first, then falls back to a 90%+ close match."""
    if not isinstance(project_name, str):
        return ""

    clean_name = " ".join(project_name.lower().split())

    if clean_name in lookup:
        return lookup[clean_name]

    matches: list[str] = difflib.get_close_matches(clean_name, lookup.keys(), n=1, cutoff=0.90)
    if matches:
        return lookup[matches[0]]

    return ""

# Shared helper used by both the initial HTML page view and the live JSON API.
#  Extracts query parameters from the URL, validates filter combinations, scans
#  the design directories, matches model stitchers from CSV, and applies assignment filters. Returns a dictionary containing the current form state, filtered results, and any validation error message. This allows both the initial page load and subsequent live searches to use the same logic for consistency.
#  assignment filters.

def run_filtered_search(request: HttpRequest) -> dict[str, object]:

  # 1. Read all 6 filter inputs from the URL query string (e.g., ?q=tree&finished=no)
  query = request.GET.get('q', '').strip()
  finished = request.GET.get('finished', 'both')
  date = request.GET.get('date', '').strip()
  priority = request.GET.get('priority', 'no')
  assigned = request.GET.get('assigned', 'all')
  stitcher = request.GET.get('stitcher', '').strip()
  error = ''

  # 2. Validate mutually exclusive filter combinations before scanning folders
  if date and priority == 'yes':
    error = (
        'Cannot filter by a specific date (YYMMDD) and sort by oldest priority'
        ' at the same time.'
    )
    results = []
  elif stitcher != '' and assigned == 'all':
    error = (
        'Cannot filter by stitcher name when assigned status is set to "all".'
        ' Please select "Has Stitcher" for assigned status when filtering by'
        ' stitcher name.'
    )
    results = []
  else:
    # 3. Run the core directory scan and name/date/status filter
    results = web_search(
        query=query,
        search_finished=finished,
        search_date=date,
        search_priority=priority,
    )

  # 4. Enrich matching results with model stitcher data from 'current wips.csv'
  if results:
    stitcher_lookup: dict[str, str] = get_stitcher_lookup()
    for item in results:
      # Only attach a model stitcher if the project is an unfinished WIP
      if not item.get('finished'):
        item['who_has'] = find_stitcher(
            str(item.get('name', '')), stitcher_lookup
        )
      else:
        item['who_has'] = ''

    # 5. Filter by whether a model stitcher is assigned ('yes' or 'no')
    if assigned == 'yes':
      results = [item for item in results if item.get('who_has')]
    elif assigned == 'no':
      results = [item for item in results if not item.get('who_has')]

    # 6. Filter by partial stitcher name (case-insensitive)
    if stitcher:
      stitcher_lower = stitcher.lower()
      results = [
          item
          for item in results
          if item.get('who_has')
          and stitcher_lower in str(item['who_has']).lower()
      ]

  # Return all form states, filtered records, and any validation error message
  return {
      'query': query,
      'finished': finished,
      'date': date,
      'priority': priority,
      'assigned': assigned,
      'stitcher': stitcher,
      'results': results,
      'error': error,
  }

# Renders the initial full HTML5/CSS page when the app or browser first loads.

def search_view(request: HttpRequest) -> HttpResponse:
  context = run_filtered_search(request)
  return render(request, 'search_app/index.html', context)

# API endpoint called asynchronously by JavaScript fetch().
# Returns raw JSON data instead of a full HTML page so the UI updates without
# reloading.

def api_search(request: HttpRequest) -> JsonResponse:
  data = run_filtered_search(request)
  return JsonResponse({'results': data['results'], 'error': data['error']})

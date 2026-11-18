from datetime import datetime
from pathlib import Path
from pprint import pprint
import sys

#set the directories to scan for cross stitch projects
finished_dir = Path('/var/home/yenot/Documents/Finished')
wip_dir = Path('/var/home/yenot/Documents/Cross stitch')

# Fixed type alias and dictionary annotations
ProjectInfo = dict[str, str | bool]
projects: dict[str, ProjectInfo] = {}

# Function to add a project to the dictionary
def add_project(folder: Path, is_finished: bool):
  stat = folder.stat()
  timestamp = getattr(stat, 'st_birthtime', stat.st_mtime)
  formatted_date = datetime.fromtimestamp(timestamp).strftime('%y%m%d %H%M')

  projects[folder.name] = {
      'created_date': formatted_date,
      'finished': is_finished,
      'path': str(folder),
  }

# Recursive function to scan directories and add projects
# will skip hidden folders and only add folders that do not contain subfolders and skips files
def scan_directory(directory: Path, is_finished: bool):
  if not directory.exists():
    return

  for item in directory.iterdir():
    if item.name.startswith('.') or not item.is_dir():
      continue

    subfolders = [
        sub
        for sub in item.iterdir()
        if sub.is_dir() and not sub.name.startswith('.')
    ]

    if subfolders:
      scan_directory(item, is_finished)
    else:
      add_project(item, is_finished)

# Function to search projects based on query, finished status, date
# if search_finished is "both", it will not filter by finished status
# if priority is "yes", it will sort by date, otherwise it will sort alphabetically by name
# priority is to assign importance for completing older projects first, so it will sort by date if priority is "yes"
# time is ignored for the sort, only the date is used for sorting
def search_designs(
    projects: dict[str, ProjectInfo],
    query: str,
    search_finished: str,
    search_date: str,
) -> dict[str, ProjectInfo]:
  results: dict[str, ProjectInfo] = {}

  if search_finished.lower().startswith('y'):
    search_bool = True
  elif search_finished.lower().startswith('n'):
    search_bool = False
  else:
    search_bool = None

  search_date = search_date.strip()

  for name, info in projects.items():
    if query != '' and query.lower() not in name.lower():
      continue

    if search_bool is not None and info['finished'] != search_bool:
      continue

    # Added missing date filter (matches YYMMDD prefix of created_date)
    if search_date != '' and not str(info['created_date']).startswith(search_date):
      continue

    results[name] = info

  return results


# --- NEW HELPER FOR DJANGO ---
def web_search(
    query: str = '',
    search_finished: str = 'both',
    search_date: str = '',
    search_priority: str = 'no',
) -> list[dict[str, str | bool]]:
  # Clear and rescan folders so new cross-stitch folders show up automatically
  projects.clear()
  scan_directory(wip_dir, is_finished=False)
  scan_directory(finished_dir, is_finished=True)

  # Enforce your priority rule: priority focuses on unfinished projects first
  if search_priority.lower() == 'yes' and search_finished == 'yes':
    search_finished = 'no'

  raw_results = search_designs(projects, query, search_finished, search_date)

  if search_priority.lower() == 'yes':
    sorted_items = sorted(
        raw_results.items(),
        key=lambda item: (item[1]['created_date'], item[0].lower()),
    )
  else:
    sorted_items = sorted(raw_results.items(), key=lambda item: item[0].lower())

  # Format as a clean list for easy rendering in HTML
  return [
      {
          'name': name,
          'created_date': info['created_date'],
          'finished': info['finished'],
          'path': info['path'],
      }
      for name, info in sorted_items
  ]


# --- EXISTING CODE (ONLY RUNS IN TERMINAL) ---
if __name__ == '__main__':
  # Get command-line arguments for search parameters
  search_query = sys.argv[1] if len(sys.argv) > 1 else ''
  search_finished = sys.argv[2] if len(sys.argv) > 2 else 'both'
  search_date = sys.argv[3] if len(sys.argv) > 3 else ''
  search_priority = sys.argv[4] if len(sys.argv) > 4 else 'no'
# validate and normalize inputs
  if search_query == '-':
    search_query = ''
  if search_date == '-':
    search_date = ''
  if search_priority == '-':
    search_priority = 'no'
  if search_finished == '-' or search_finished == 'yes':
    if search_priority.lower() == 'yes':
      search_finished = 'no'
    elif search_priority.lower() == '-':
      search_finished = 'both'
# if search date is provided, search_priority must be "no" (cannot filter by date and sort by priority at the same time)
  while search_date != '' and search_priority.lower() == 'yes':
    print(
        'Cannot select both date and priority. Selecting date YYMMDD returns'
        ' projects with that date. Selecting priority sorts by date.'
    )
    search_date = input('Enter a search date (or leave blank): ').strip()
    search_priority = input('Enter search priority (yes/no): ').strip().lower()

# make sure search_priority is either "yes" or "no"
  while search_priority.lower() not in ('yes', 'no'):
    search_priority = input('Enter search priority (yes/no): ').strip().lower()

# make sure search_finished is either "yes", "no", or "both"
  while search_finished.lower() not in ('yes', 'no', 'both'):
    search_finished = (
        input('Search finished projects? (yes/no/both): ').strip().lower()
    )

# scan the directories for cross stitch projects
# clear the projects dictionary before scanning to avoid duplicates
  projects.clear()  
  scan_directory(wip_dir, is_finished=False)
  scan_directory(finished_dir, is_finished=True)

# search the projects based on the provided parameters
  search_results: dict[str, ProjectInfo] = search_designs(
      projects, search_query, search_finished, search_date
  )

# sort the results based on the search_priority parameter
  if search_priority.lower() == 'yes':
    search_results = dict(
        sorted(
            search_results.items(),
            key=lambda item: (item[1]['created_date'], item[0].lower()),
        )
    )
  else:
    search_results = dict(sorted(search_results.items()))

  pprint(search_results, sort_dicts=False)

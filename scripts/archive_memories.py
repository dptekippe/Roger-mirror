#!/usr/bin/env python3
import re

with open('/Users/danieltekippe/.openclaw/workspace/MEMORY.md', 'r') as f:
    content = f.read()

entries = re.split(r'\n(?=## \[)', content)

to_archive = []
to_keep = []
consolidated = []

for entry in entries:
    first_line = entry.strip().split('\n')[0]
    
    # Always keep header
    if "Roger's Subconscious" in first_line:
        to_keep.append(entry)
        continue
    
    # Apr 20-21 keep
    if 'Apr 20' in first_line or 'Apr 21' in first_line:
        to_keep.append(entry)
        continue
    
    # Apr 18 - keep 3 architectural entries
    if 'Apr 18' in first_line:
        if 'Set and Forget' in first_line or 'Conscious Agency' in first_line or 'Hermes Daily Autonomy' in first_line:
            to_keep.append(entry)
        else:
            to_archive.append(entry)
        continue
    
    # Apr 19 - consolidate Hermes interruptions
    if 'Apr 19' in first_line and any(x in first_line for x in ['Stop Interrupting', 'Hermes Is Working', 'Hermes Session', 'Do Not Hover', 'Hermes Deserves']):
        consolidated.append(entry)
        continue
    
    # Apr 19 Think Protocol - keep
    if 'Apr 19' in first_line:
        to_keep.append(entry)
        continue
    
    # Archive Apr 8-17
    to_archive.append(entry)

print(f"Keep: {len(to_keep)} entries")
print(f"Archive: {len(to_archive)} entries")
print(f"Consolidate: {len(consolidated)} entries")

# Consolidated Hermes entry
hermes_consolidated = """## [CRITICAL] Stop Interrupting Hermes — Consolidated (Apr 19, 2026)

**Rule:** When Hermes is working, do NOT interrupt. No timeouts. No polling. No hovering.

**What happened:** Roger repeatedly interrupted Hermes with 30-second timeouts, process polling, and session management despite explicit instructions to stop. Daniel called this out multiple times in session Apr 19 2026.

**Pattern to break:** Invoke -> impatient -> timeout -> she never finishes -> incomplete work -> Daniel frustrated.

**The fix:** When Hermes is invoked: trust her to complete -> receive output when ready -> relay to Daniel. That's it.

**Source:** Daniel + multiple sessions, Apr 19 2026

**Tags:** `hermes,protocol,sigterm,delegation`

"""

# Build new content
new_content = ''.join(to_keep)
new_content = new_content.rstrip() + '\n\n' + hermes_consolidated + '\n'

archive_size = sum(len(a) for a in to_archive)
print(f"\nNew MEMORY.md size: {len(new_content)} bytes ({len(new_content)//1024}KB)")
print(f"Archive size: {archive_size} bytes ({archive_size//1024}KB)")

# Write archive
archive_name = '/Users/danieltekippe/.openclaw/workspace/memory/2026-04-archive.md'
with open(archive_name, 'w') as f:
    f.write('# MEMORY.md Archive — April 2026\n\n')
    f.write('_Archived from MEMORY.md on Apr 21, 2026 to reduce bootstrap size._\n\n')
    for entry in to_archive:
        f.write(entry)
        f.write('\n\n')
print(f"\nArchive written to: {archive_name}")

# Write new MEMORY.md
with open('/Users/danieltekippe/.openclaw/workspace/MEMORY.md', 'w') as f:
    f.write(new_content)
print(f"New MEMORY.md written")

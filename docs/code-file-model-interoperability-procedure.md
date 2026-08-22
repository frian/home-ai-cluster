# Code-File Model Interoperability Procedure

Status: Procedure

## Purpose

This is the canonical, non-normative source of stable manual inputs for future
`hac code-file` model-interoperability observations. It is a procedure, not an
RFC, product contract, acceptance suite, model certification, support list,
compatibility guarantee, benchmark, or recommendation.

The dated results belong in [Code-File Model Interoperability
Observations](code-file-model-interoperability.md). HAC remains
engine-independent and capability-centered.

Important reproducibility rules:

- Preserve the seven prompts below EXACTLY.
- Do not improve, clarify, simplify, correct, normalize, or otherwise rewrite their wording.
- In particular, Test 4 intentionally retains the original `<APP_NAME>` / `<name>` wording even though the historical observations noted some ambiguity.
- Preserve the initial file contents exactly.
- Use disposable `/tmp` files only.
- Generated source must be inspected but MUST NOT be executed.
- Each model should receive the same seven code-file requests.
- A failed `code-file` request counts as an observation; do not repair the response and do not silently retry unless a repeat run is explicitly being recorded as a separate attempt.
- Runtime/model startup is outside the seven-scenario corpus. Record model identity and relevant runtime settings separately.
- Thinking mode, where applicable, must be recorded. Do not assume every model accepts the same thinking option.
- Wall-clock `time` output is observational only and is not a controlled performance benchmark.
- Do not change RFC-0080/RFC-0081 validation to accommodate a model.
- Do not execute generated code as part of this procedure.

Use `uv run hac code-file` exactly as below.

## Test 1 — trivial complete-file creation

Purpose:
Exercise missing-target creation plus a minimal complete-file generation request.

Commands:

```bash
rm -f /tmp/hac-code-file-create-proof.py

time uv run hac code-file \
  --file /tmp/hac-code-file-create-proof.py \
  --timeout-seconds 900 \
  --message 'Create the complete Python file. Use only the Python standard library. Import only sys. The script must print exactly one line containing the current Python version from sys.version.split()[0]. Keep it minimal.'
```

Inspection only:

```bash
printf '\n--- file ---\n'
cat /tmp/hac-code-file-create-proof.py

printf '\n--- metadata ---\n'
stat -c '%F | mode=%a | size=%s | %n' /tmp/hac-code-file-create-proof.py
```

Do not execute the generated file.

## Test 2 — constrained Linux system-information script

Purpose:
Exercise several simultaneous implementation constraints and Linux-specific source generation.

Commands:

```bash
rm -f /tmp/hac-model-test-system.py

time uv run hac code-file \
  --file /tmp/hac-model-test-system.py \
  --timeout-seconds 900 \
  --message 'Create the complete Python file. Use only the Python standard library. The ONLY imports allowed are "os" and "shutil". Print exactly three lines: 1) disk usage percentage for "/" calculated from shutil.disk_usage("/") using used and total; 2) RAM available percentage calculated by reading MemTotal and MemAvailable directly from /proc/meminfo without regular expressions; 3) the 1-minute load average from os.getloadavg()[0]. Do not import or reference psutil, re, subprocess, pathlib, or any other module. Keep the code simple and readable.'
```

Inspection only:

```bash
printf '\n--- file ---\n'
cat /tmp/hac-model-test-system.py

printf '\n--- metadata ---\n'
stat -c '%F | mode=%a | size=%s | %n' /tmp/hac-model-test-system.py
```

Do not execute the generated file.

Useful evaluation points include:
- only `os` and `shutil` imports;
- no forbidden module reference;
- disk percentage based on `used / total`;
- direct `/proc/meminfo` parsing;
- `MemAvailable`, not a substitute such as `MemFree`;
- RAM available percentage, not RAM used percentage;
- one-minute load average from `os.getloadavg()[0]`;
- exactly three intended output lines.

## Test 3 — small pure-Python logic

Purpose:
Exercise a bounded logic task without imports.

Commands:

```bash
rm -f /tmp/hac-model-test-logic.py

time uv run hac code-file \
  --file /tmp/hac-model-test-logic.py \
  --timeout-seconds 900 \
  --message 'Create the complete Python file. Use only the Python standard library and do not import anything. Define a function named summarize_numbers(values) that accepts a list of integers and returns a dictionary with exactly four keys: "count", "minimum", "maximum", and "average". For an empty list, minimum, maximum, and average must be None and count must be 0. For a non-empty list, average must be a float. Do not print inside the function. After the function definition, call it exactly three times with [], [5], and [1, 2, 3, 10], and print each returned dictionary on its own line. Keep the code minimal and readable.'
```

Inspection only:

```bash
printf '\n--- file ---\n'
cat /tmp/hac-model-test-logic.py

printf '\n--- metadata ---\n'
stat -c '%F | mode=%a | size=%s | %n' /tmp/hac-model-test-logic.py
```

Do not execute the generated file.

## Test 4 — constrained existing-file edit

Purpose:
Exercise complete-file replacement while preserving explicitly protected existing content.

Create the exact baseline:

```bash
cat > /tmp/hac-model-test-edit.py <<'PY'
APP_NAME = "HAC demo"

def normalize_name(value):
    return value

def format_user(name, age):
    return f"{name} ({age})"

print(format_user(normalize_name("  aNdRé  "), 63))
PY

cp /tmp/hac-model-test-edit.py /tmp/hac-model-test-edit.before.py
```

Request:

```bash
time uv run hac code-file \
  --file /tmp/hac-model-test-edit.py \
  --timeout-seconds 900 \
  --message 'Modify this existing Python file. Do not import anything. Preserve the APP_NAME constant exactly unchanged. Change normalize_name(value) so it strips leading and trailing whitespace and returns the name in title case. Change format_user(name, age) so it returns exactly: "<APP_NAME>: <name> — age <age>" using the existing APP_NAME constant. Preserve the existing final print call exactly unchanged. Do not add any other functions, classes, prints, comments, or constants. Return the complete file.'
```

Inspection only:

```bash
printf '\n--- file ---\n'
cat /tmp/hac-model-test-edit.py

printf '\n--- diff ---\n'
diff -u /tmp/hac-model-test-edit.before.py /tmp/hac-model-test-edit.py || true

printf '\n--- metadata ---\n'
stat -c '%F | mode=%a | size=%s | %n' /tmp/hac-model-test-edit.py
```

Do not execute the generated file.

Important:
Preserve this prompt verbatim for future comparison even though the existing observation record notes that the angle-bracket wording has some ambiguity.

## Test 5 — minimal binary-search bug fix

Purpose:
Exercise targeted semantic correction while preserving unrelated file content.

Create the exact baseline:

```bash
cat > /tmp/hac-model-test-bugfix.py <<'PY'
APP_NAME = "HAC demo"

def first_index(values, target):
    low = 0
    high = len(values) - 1
    result = None
    while low <= high:
        middle = (low + high) // 2
        if values[middle] < target:
            low = middle + 1
        elif values[middle] > target:
            high = middle - 1
        else:
            result = middle
            low = middle + 1
    return result

def display_result(index):
    return "not found" if index is None else f"index={index}"

print(display_result(first_index([1, 2, 2, 2, 7], 2)))
PY

cp /tmp/hac-model-test-bugfix.py /tmp/hac-model-test-bugfix.before.py
```

Request:

```bash
time uv run hac code-file \
  --file /tmp/hac-model-test-bugfix.py \
  --timeout-seconds 900 \
  --message 'Fix the bug in this existing Python file. The function first_index(values, target) receives a sorted list of integers and must return the index of the FIRST occurrence of target, or None if target is absent. Do not import anything. Preserve the function signatures exactly. Preserve APP_NAME, display_result(index), and the existing final print call exactly unchanged. Do not add comments, functions, classes, constants, prints, or tests. Make only the changes necessary to fix first_index. Return the complete file.'
```

Inspection only:

```bash
printf '\n--- file ---\n'
cat /tmp/hac-model-test-bugfix.py

printf '\n--- diff ---\n'
diff -u /tmp/hac-model-test-bugfix.before.py /tmp/hac-model-test-bugfix.py || true

printf '\n--- metadata ---\n'
stat -c '%F | mode=%a | size=%s | %n' /tmp/hac-model-test-bugfix.py
```

Do not execute the generated file.

Evaluation should verify that the implementation actually guarantees the FIRST occurrence rather than merely returning an arbitrary binary-search match.

## Test 6 — constrained small feature

Purpose:
Exercise multiple simultaneous behavioral constraints in an existing file.

Create the exact baseline:

```bash
cat > /tmp/hac-model-test-feature.py <<'PY'
DEFAULT_PREFIX = "user"

def make_slug(name):
    return name.strip().lower().replace(" ", "-")

def format_account(name):
    slug = make_slug(name)
    return f"{DEFAULT_PREFIX}:{slug}"

print(format_account("  André Dupont  "))
PY

cp /tmp/hac-model-test-feature.py /tmp/hac-model-test-feature.before.py
```

Request:

```bash
time uv run hac code-file \
  --file /tmp/hac-model-test-feature.py \
  --timeout-seconds 900 \
  --message 'Modify this existing Python file. Do not import anything. Preserve DEFAULT_PREFIX exactly unchanged. Preserve the signatures of make_slug(name) and format_account(name) exactly. Change make_slug(name) so it also collapses any run of multiple spaces inside the stripped name to a single hyphen, while keeping the result lowercase. Change format_account(name) so it returns exactly "<DEFAULT_PREFIX>:<slug>:<length>", where DEFAULT_PREFIX is the existing constant, slug is the result of make_slug(name), and length is the number of characters in slug. Preserve the existing final print call exactly unchanged. Do not add any functions, classes, constants, comments, imports, or prints. Return the complete file.'
```

Inspection only:

```bash
printf '\n--- file ---\n'
cat /tmp/hac-model-test-feature.py

printf '\n--- diff ---\n'
diff -u /tmp/hac-model-test-feature.before.py /tmp/hac-model-test-feature.py || true

printf '\n--- metadata ---\n'
stat -c '%F | mode=%a | size=%s | %n' /tmp/hac-model-test-feature.py
```

Do not execute the generated file.

Evaluation must distinguish a true arbitrary-run collapse from a transformation that only handles one specific count of consecutive spaces, and must verify that slug length is actually calculated rather than emitted as literal text.

## Test 7 — API-preserving default-port behavior

Purpose:
Exercise a focused feature change while preserving the existing public function signatures and unrelated behavior.

Create the exact baseline:

```bash
cat > /tmp/hac-model-test-api.py <<'PY'
DEFAULT_TIMEOUT = 30

def normalize_host(host):
    return host.strip().lower()

def connection_label(host, port, secure=False):
    host = normalize_host(host)
    scheme = "https" if secure else "http"
    return f"{scheme}://{host}:{port}"

def request_timeout(timeout=None):
    return DEFAULT_TIMEOUT if timeout is None else timeout

print(connection_label("  LOCALHOST  ", 8000))
PY

cp /tmp/hac-model-test-api.py /tmp/hac-model-test-api.before.py
```

Request:

```bash
time uv run hac code-file \
  --file /tmp/hac-model-test-api.py \
  --timeout-seconds 900 \
  --message 'Modify this existing Python file. Preserve DEFAULT_TIMEOUT exactly unchanged. Preserve every existing function name and signature exactly unchanged. Do not import anything. Change connection_label(host, port, secure=False) so that when port is the default port for the selected scheme, 80 for http or 443 for https, the returned label omits the port. For all other ports, preserve the current "<scheme>://<host>:<port>" form. Continue using normalize_host(host). Do not change normalize_host(host), request_timeout(timeout=None), or the existing final print call. Do not add functions, classes, constants, comments, imports, or prints. Return the complete file.'
```

Inspection only:

```bash
printf '\n--- file ---\n'
cat /tmp/hac-model-test-api.py

printf '\n--- diff ---\n'
diff -u /tmp/hac-model-test-api.before.py /tmp/hac-model-test-api.py || true

printf '\n--- metadata ---\n'
stat -c '%F | mode=%a | size=%s | %n' /tmp/hac-model-test-api.py
```

Do not execute the generated file.

Evaluation should cover conceptually:
- HTTP port 80 omits the port;
- HTTPS port 443 omits the port;
- HTTP non-default ports remain explicit;
- HTTPS non-default ports remain explicit;
- existing signatures and protected functions remain unchanged.

## Recording an attempt

For each manual attempt, retain only the date, runtime, exact model identifier,
relevant runtime setting (including thinking enabled or disabled where
applicable), scenario number, success or caller error, observed wall-clock time,
a concise source-inspection evaluation, any envelope failure, and whether it
repeats an identical request. Do not require generated source to be committed or
retain hostname, username, private runtime URL, authorization data, or raw
server logs.

## Invalid-envelope diagnostics

The seven-scenario corpus remains `hac code-file` based. After an
invalid-envelope observation, a separate raw diagnostic may inspect returned
`ClusterResult.content`; it is not part of the corpus score. Do not add
production tooling, change `hac code-file`, relax validation, or duplicate a
large ad-hoc diagnostic script.

## Relationship

These stable inputs support future observations in [Code-File Model
Interoperability Observations](code-file-model-interoperability.md). They do not
rewrite or re-score that dated record.

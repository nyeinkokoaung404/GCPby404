import requests
import json
import random
import os
import asyncio
from playwright.async_api import async_playwright, expect
from datetime import datetime, date

# --- Configuration for Playwright GitHub Login ---
GITHUB_USERNAME = os.environ.get("DENO_GH_USER", "playbillbesjljljlj@gmail.com")
GITHUB_PASSWORD = os.environ.get("DENO_GH_PASS", "jhfjhfgjfh")
# --- End of Playwright Configuration ---

# --- Cookie Persistence Configuration ---
COOKIES_FILE_PATH = "deno_cookies.json"
# ---

DENO_LOGIN_URL = "https://dash.deno.com/login?redirect=%2F"
DENO_ME_API_URL = "https://dash.deno.com/_api/me"
DENO_DASHBOARD_URL = "https://dash.deno.com/"

def load_cookies_from_file(filepath=COOKIES_FILE_PATH):
    """Loads cookies and their generation date from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'cookies' in data and 'generated_date' in data:
                cookies = data['cookies']
                generated_date = data['generated_date']
                if isinstance(cookies, dict) and ('token' in cookies or 'deno_auth_ghid' in cookies):
                    print(f"Successfully loaded cookies and date from {filepath}")
                    return cookies, generated_date
                else:
                    print(f"Invalid cookie format inside {filepath}. Deleting file.")
                    os.remove(filepath)
                    return None, None
            else:
                print(f"Invalid or incomplete data format in {filepath}. Deleting file.")
                os.remove(filepath)
                return None, None
    except FileNotFoundError:
        print(f"Cookie file {filepath} not found.")
        return None, None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {filepath}. File might be corrupted. Deleting file.")
        os.remove(filepath)
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred while loading cookies from {filepath}: {e}")
        return None, None

def save_cookies_to_file(cookies_dict, filepath=COOKIES_FILE_PATH):
    """Saves cookies and the current date to a JSON file."""
    try:
        current_date_str = date.today().isoformat()
        data_to_save = {
            "cookies": cookies_dict,
            "generated_date": current_date_str
        }
        with open(filepath, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"Cookies and generation date ({current_date_str}) saved to {filepath}")
    except Exception as e:
        print(f"An error occurred while saving cookies to {filepath}: {e}")

async def validate_cookies(cookie_dict_to_validate, base_headers):
    """Validates cookies by making a test request to the Deno dashboard URL."""
    if not cookie_dict_to_validate:
        print("No cookies provided for validation.")
        return False
    
    temp_headers = base_headers.copy()
    temp_headers['cookie'] = "; ".join([f"{name}={value}" for name, value in cookie_dict_to_validate.items()])
    
    print(f"Validating cookies with a request to {DENO_DASHBOARD_URL}...")
    try:
        response = requests.get(DENO_DASHBOARD_URL, headers=temp_headers, allow_redirects=False, timeout=10)
        if response.status_code == 200:
            if "Welcome back" in response.text or "Sign out" in response.text or "Dashboard" in response.text or "Your projects" in response.text:
                print(f"Cookies are valid. Successfully accessed Deno Dashboard.")
                return True
            else:
                print(f"Cookie validation failed. Status: {response.status_code}. Response content does not indicate logged-in state.")
                return False
        elif response.status_code in [302, 303, 307, 308]:
            location = response.headers.get('Location', 'N/A')
            if "login" in location or "oauth" in location:
                print(f"Cookie validation failed. Redirected to login/auth page. Status: {response.status_code}, Location: {location}")
                return False
            else:
                print(f"Cookie validation failed. Unexpected redirect. Status: {response.status_code}, Location: {location}")
                return False
        else:
            print(f"Cookie validation failed. Unexpected Status: {response.status_code}, Response: {response.text[:100]}...")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error during cookie validation request: {e}")
        return False

async def get_deno_auth_cookies_via_github():
    """Automates the login process to dash.deno.com using GitHub OAuth and extracts cookies."""
    if GITHUB_USERNAME == "your_github_username@example.com" or GITHUB_PASSWORD == "your_github_password":
        print("CRITICAL: GitHub credentials are not set or are using default placeholder values.")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        print(f"Playwright: Navigating to Deno Dashboard login page: {DENO_LOGIN_URL}...")
        
        try:
            await page.goto(DENO_LOGIN_URL, wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f"Playwright Error: Navigating to Deno login page failed: {e}")
            await browser.close()
            return None

        try:
            github_login_button = page.locator('button:has-text("Continue with GitHub")')
            print("Playwright: Waiting for 'Continue with GitHub' button...")
            await expect(github_login_button).to_be_visible(timeout=20000)
            await expect(github_login_button).to_be_enabled(timeout=20000)
            print("Playwright: Clicking 'Continue with GitHub' button...")
            await github_login_button.click()
            await page.wait_for_load_state('networkidle', timeout=30000)
        except Exception as e:
            print(f"Playwright Error (Step 1 Deno login button): {e}")
            await page.screenshot(path="error_playwright_deno_github_button.png")
            await browser.close()
            return None

        print(f"Playwright: Current URL after clicking GitHub button: {page.url}")
        
        try:
            if "github.com/login" in page.url and not "oauth/authorize" in page.url:
                print("Playwright: On GitHub login page. Filling credentials...")
                await page.locator('input#login_field').fill(GITHUB_USERNAME, timeout=15000)
                await page.locator('input#password').fill(GITHUB_PASSWORD, timeout=15000)
                await page.locator('input[type="submit"][name="commit"]').click(timeout=15000)
                await page.wait_for_load_state('networkidle', timeout=30000)
                print(f"Playwright: URL after GitHub sign-in attempt: {page.url}")
            else:
                print("Playwright: Skipped GitHub login form (possibly already logged in or on auth page).")
        except Exception as e:
            print(f"Playwright Error (Step 2 GitHub Login): {e}")
            await page.screenshot(path="error_playwright_github_login.png")
            await browser.close()
            return None

        if "github.com/login/oauth/authorize" in page.url:
            print("Playwright: On GitHub authorization page. Attempting to click 'Authorize'...")
            try:
                authorize_button = page.locator('button[type="submit"][name="authorize"]').or_(page.locator('button#js-oauth-authorize-btn'))
                if await authorize_button.count() > 0:
                    await authorize_button.first().click(timeout=20000)
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    print("Playwright: Clicked 'Authorize' button on GitHub.")
                else:
                    print("Playwright: Authorize button not found, assuming already authorized or a different flow.")
            except Exception as e:
                print(f"Playwright Warning (Step 3 GitHub Auth - authorize button click failed): {e}")
                await page.screenshot(path="error_playwright_github_auth.png")

        print(f"Playwright: Current URL before final Deno redirect check: {page.url}")
        try:
            await page.wait_for_url(
                lambda url: "dash.deno.com" in url and "login" not in url and "error" not in url,
                timeout=45000
            )
            print(f"Playwright: Successfully redirected to Deno Dashboard: {page.url}")
        except Exception as e:
            print(f"Playwright Error (Step 4 Deno Redirect failed): {e}")
            await page.screenshot(path="error_playwright_deno_redirect.png")
            await browser.close()
            return None

        cookies = await context.cookies()
        deno_cookies_dict = {}
        for cookie in cookies:
            if "deno.com" in cookie.get('domain', '') and cookie.get('name') in ['token', 'deno_auth_ghid', 'deno_auth']:
                deno_cookies_dict[cookie['name']] = cookie['value']
        
        if not any(key in deno_cookies_dict for key in ['token', 'deno_auth_ghid']):
            print("Playwright Warning: Essential Deno cookies ('token', 'deno_auth_ghid') not found after login.")
            await page.screenshot(path="warning_playwright_missing_cookies.png")
            await browser.close()
            return None

        await browser.close()
        print(f"Playwright: Successfully extracted {len(deno_cookies_dict)} Deno cookies.")
        return deno_cookies_dict

async def get_active_cookies(base_headers):
    """Tries to load cookies from file, validates their date, and refreshes via Playwright if necessary."""
    cookies, saved_date_str = load_cookies_from_file()
    current_date_str = date.today().isoformat()
    
    if cookies and saved_date_str == current_date_str:
        print(f"Cookies from {saved_date_str} are available and from today. Validating them...")
        if await validate_cookies(cookies, base_headers):
            print("Cookies are valid and fresh for today. Skipping Playwright.")
            return cookies
        else:
            print("Cookies from today are invalid. Attempting to refresh via Playwright login.")
    elif cookies and saved_date_str != current_date_str:
        print(f"Cookies found from {saved_date_str}, but today is {current_date_str}. Attempting to validate and potentially refresh.")
        if await validate_cookies(cookies, base_headers):
            print("Cookies are still valid despite being from a previous day. Updating date.")
            save_cookies_to_file(cookies)
            return cookies
        else:
            print("Cookies from a previous day are invalid. Attempting to refresh via Playwright login.")
            if os.path.exists(COOKIES_FILE_PATH):
                os.remove(COOKIES_FILE_PATH)
                print(f"Removed old invalid cookie file: {COOKIES_FILE_PATH}")
    else:
        print("No valid cookies found or file corrupted. Attempting to login via Playwright.")

    refreshed_cookies = await get_deno_auth_cookies_via_github()
    if refreshed_cookies:
        save_cookies_to_file(refreshed_cookies)
        return refreshed_cookies
    
    print("CRITICAL: Failed to obtain valid cookies even after attempting Playwright login.")
    return None

# --- Main Script Logic ---
base_custom_headers = {
    'accept': 'application/json',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://dash.deno.com',
    'priority': 'u=1, i',
    'referer': 'https://dash.deno.com/subhosting/new',
    'sec-ch-ua': '"Chromium";v="125", "Google Chrome";v="125", "Not.A/Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'x-api-client': 'true'
}

async def perform_deno_dashboard_api_call(url, method, payload, headers, retry_attempts=2):
    """Performs a Deno Dashboard API call with a retry mechanism."""
    for attempt in range(retry_attempts):
        print(f"\nAttempt {attempt + 1}/{retry_attempts} for {method} {url}")
        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=payload)
            elif method == 'GET':
                response = requests.get(url, headers=headers, params=payload)
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code in [401, 403] and attempt < retry_attempts - 1:
                print(f"Authentication/Authorization error ({http_err.response.status_code}). Attempting to refresh cookies...")
                new_cookie_data = await get_active_cookies(base_custom_headers.copy())
                if new_cookie_data:
                    headers['cookie'] = "; ".join([f"{name}={value}" for name, value in new_cookie_data.items()])
                    print("Cookies refreshed. Retrying API call.")
                else:
                    print("Failed to refresh cookies. Cannot retry API call.")
                    raise
            else:
                print(f"HTTP error occurred during API call: {http_err}")
                print(f"Status Code: {http_err.response.status_code}, Response Body: {http_err.response.text}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred during API call: {e}")
            raise
    return None

async def main_script_logic():
    global organization_id, generated_token

    print("Initializing cookie management...")
    active_cookie_data = await get_active_cookies(base_custom_headers.copy())

    if not active_cookie_data:
        print("FATAL: Could not obtain valid Deno authentication cookies. Exiting script.")
        exit(1)

    final_custom_headers = base_custom_headers.copy()
    final_custom_headers['cookie'] = "; ".join([f"{name}={value}" for name, value in active_cookie_data.items()])
    print(f"Successfully prepared headers with active cookies (first 70 chars): {final_custom_headers['cookie'][:70]}...")

    # --- First Request: Create Organization ---
    url_create_organization = 'https://dash.deno.com/_api/organizations'
    random_number = random.randint(1000, 9999)
    organization_name = f"Modsbots-Auto-{random_number}"
    payload_create_organization = {
        "name": organization_name,
        "subhostingEnabled": False
    }

    print(f"\n--- First Request: Creating Organization '{organization_name}' ---")
    try:
        response_json_org = await perform_deno_dashboard_api_call(
            url_create_organization, 'POST', payload_create_organization, final_custom_headers
        )
        if response_json_org:
            print("Organization creation successful!")
            organization_id = response_json_org.get('id')
            if organization_id:
                print("Organization ID:", organization_id)
            else:
                print("ERROR: 'id' field was not found in the organization creation response.")
                print("Response JSON:", response_json_org)
        else:
            print("Organization creation failed after retries.")
    except Exception as e:
        print(f"Final failure creating organization: {e}")

    # --- Second Request: Create Token (if organization_id was obtained) ---
    if organization_id:
        url_create_token = f'https://dash.deno.com/_api/organizations/{organization_id}/tokens'
        payload_create_token = {"description": "modsbots_auto_token", "expiresAt": None}
        print(f"\n--- Second Request: Creating Token for Org ID {organization_id} ---")
        try:
            response_json_token = await perform_deno_dashboard_api_call(
                url_create_token, 'POST', payload_create_token, final_custom_headers
            )
            if response_json_token:
                print("Token creation successful!")
                if isinstance(response_json_token, list) and len(response_json_token) > 0 and isinstance(response_json_token[0], str):
                    generated_token = response_json_token[0]
                    print("Generated Token (first 10 chars):", generated_token[:10] + "...")
                else:
                    print("ERROR: Could not find the token string in the token creation response.")
                    print("Response JSON:", response_json_token)
            else:
                print("Token creation failed after retries.")
        except Exception as e:
            print(f"Final failure creating token: {e}")
    else:
        print("\nSkipping token creation as organization ID was not obtained.")

    # --- Deno Deploy API Operations ---
    print("\n" + "="*50)
    print("--- Deno Deploy API Operations ---")
    print("="*50 + "\n")

    accessToken = generated_token
    orgId = organization_id
    API_V1_URL = "https://api.deno.com/v1"

    if not accessToken:
        print("Error: Access token (generated_token) not available for Deno Deploy operations.")
    if not orgId:
        print("Error: Organization ID not available for Deno Deploy operations.")

    project = None
    if accessToken and orgId:
        deno_deploy_headers = {
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
            "User-Agent": base_custom_headers['user-agent'],
            "Accept": "application/json",
        }
        project_payload_name = f"modsbots-deploy-{random.randint(1000,9999)}"
        print(f"Creating a new Deno Deploy project '{project_payload_name}' in organization '{orgId}'...")
        pr_response = None
        try:
            pr_response = requests.post(
                f"{API_V1_URL}/organizations/{orgId}/projects",
                headers=deno_deploy_headers,
                json={"name": project_payload_name},
            )
            pr_response.raise_for_status()
            project = pr_response.json()
            print(f"Project created: {project.get('name')} (ID: {project.get('id')})")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error creating Deno Deploy project: {http_err}")
            if pr_response is not None:
                print(f"Response status: {pr_response.status_code}, Body: {pr_response.text}")
            project = None
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred creating Deno Deploy project: {e}")
            project = None

        if project and project.get('id'):
            print(f"Deploying 'hello world' server to Deno Deploy project '{project['name']}'...")
            dr_response = None
            try:
                dr_response = requests.post(
                    f"{API_V1_URL}/projects/{project['id']}/deployments",
                    headers=deno_deploy_headers,
                    json={
                        "entryPointUrl": "main.ts",
                        "assets": {
                            "main.ts": {
                                "kind": "file",
                                "content": f'Deno.serve((_req) => new Response("Hello, world! Deployed by Modsbots via Automated Script. Current time: {datetime.now()}."));',
                                "encoding": "utf-8",
                            },
                        },
                        "envVars": {},
                    },
                )
                dr_response.raise_for_status()
                deployment = dr_response.json()
                print(f"Deployment successful! Status: {dr_response.status_code}")
                
                project_name_from_deploy = project.get('name')
                if project_name_from_deploy:
                    print(f"Visit your site (primary project URL): https://{project_name_from_deploy}.deno.dev")
                
                if deployment and deployment.get('domains') and len(deployment['domains']) > 0:
                    print("Deployment specific domains:")
                    for domain in deployment['domains']:
                        print(f" - https://{domain}")
                elif deployment and deployment.get('id') and project_name_from_deploy:
                    print(f"Fallback deployment URL: https://{project_name_from_deploy}-{deployment.get('id')}.deno.dev")
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error deploying server to Deno Deploy: {http_err}")
                if dr_response is not None:
                    print(f"Response status: {dr_response.status_code}, Body: {dr_response.text}")
            except requests.exceptions.RequestException as e:
                print(f"An unexpected error occurred deploying server to Deno Deploy: {e}")
        else:
            print("Skipping Deno Deploy deployment as project was not successfully created or ID is missing.")
    else:
        print("Skipping Deno Deploy API operations due to missing Deno Deploy access token or organization ID.")

    print("\n--- Script Finished ---")

if __name__ == "__main__":
    organization_id = None
    generated_token = None
    asyncio.run(main_script_logic())

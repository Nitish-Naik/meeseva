from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

driver = webdriver.Chrome()

try:
    driver.get('https://ts.meeseva.telangana.gov.in/meeseva/home.htm')
    wait = WebDriverWait(driver, 10)
    meeseva_centres = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'MeeSeva Centres')))
    ActionChains(driver).move_to_element(meeseva_centres).perform()
    time.sleep(1)
    authorized_service_providers = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Authorized Service Provider')))
    authorized_service_providers.click()
    time.sleep(3)
    target_value = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[@onclick=\"getDetailedDetails('NIZAMABAD','Total')\" and text()='364']"))
    )
    target_value.click()
    print("173 clicked")
    time.sleep(3)

    table = driver.find_element(By.XPATH, "//table[@id='dgDispatch']")
    rows = table.find_elements(By.TAG_NAME, "tr")
    data = []
    headers = [header.text for header in rows[0].find_elements(By.TAG_NAME, "th")]
    for row in rows[1:]:
        cells = row.find_elements(By.TAG_NAME, "td")
        row_data = {headers[i]: cells[i].text for i in range(len(cells))}
        data.append(row_data)

    with open("nizamabad_data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    print("Data extracted and saved to nizamabad_data.json")

finally:
    time.sleep(5)
    driver.quit()

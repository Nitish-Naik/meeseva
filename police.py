


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import json
import logging

class MeesevaScraper:
    def __init__(self, url):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.url = url
        self.services = []

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='scraper.log'
        )
        self.logger = logging.getLogger(__name__)

    def start(self):
        try:
            self.driver.get(self.url)
            self.driver.maximize_window()
            WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'serviceTxt')))
            self.click_police()
            self.extract_service_links()
            self.save_to_json('Police.json')
        except Exception as e:
            self.logger.error(f"Fatal error in start(): {e}")
        finally:
            self.driver.quit()

    def click_police(self):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                registration_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, 'Police'))
                )
                registration_link.click()
                WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, 'serDesc')))
                return
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed to click Police link: {e}")
                if attempt == max_attempts - 1:
                    raise Exception("Failed to click Police link after maximum attempts")
                time.sleep(2)

    def extract_service_links(self):
        try:
            services = self.driver.find_elements(By.XPATH, "//td[3]/a")
            service_count = len(services)
            self.logger.info(f"Found {service_count} services to process")

            for index in range(service_count):
                if index == 24:  
                    continue
                    
                try:
                    services = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//td[3]/a"))
                    )
                    service = services[index]
                    service_name = service.text
                    self.logger.info(f"Processing service {index + 1}/{service_count}: {service_name}")

    
                    self.retry_click(service)

                    
                    service_data = self.extract_service_details(index, service_name)
                    
                    if service_data:
                        self.services.append(service_data)
                        self.logger.info(f"Successfully extracted details for {service_name}")
                    
                    self.navigate_back_to_services()

                except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                    self.logger.error(f"Error processing service at index {index}: {e}")
                    self.handle_error_state()
                    continue

        except Exception as e:
            self.logger.error(f"Fatal error in extract_service_links: {e}")

    def extract_service_details(self, index, service_name):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='panel-title tCenter']"))
            )


            details = {
                'S.No': index + 1,
                'Service Name': service_name,
                'Fee Label': self.safe_get_text_if_exists("(//div[@class='panel-title tCenter'])[1]"),
                'Fee Value': self.safe_get_text_if_exists("(//div[@class='labelValue tCenter'])[1]"),
                'Timeline Label': self.safe_get_text_if_exists("(//div[@class='panel-title tCenter'])[2]"),
                'Timeline Value': self.safe_get_text_if_exists("(//div[@class='labelValue tCenter'])[2]"),
                'Description': self.safe_get_text_if_exists("//td[b[text()='Description']]/following-sibling::td"),
                'Service Delivery Channels': self.safe_get_text_if_exists("//td[b[text()='Service Delivery Channels']]/following-sibling::td"),
                'Service Timings': self.safe_get_text_if_exists("//td[b[text()='Service Timings']]/following-sibling::td"),
                'Service Payment Modes': self.safe_get_text_if_exists("//td[b[text()='Service Payment Modes']]/following-sibling::td")
            }


            missing_fields = [k for k, v in details.items() if v == "N/A"]
            if missing_fields:
                self.logger.warning(f"Missing fields for {service_name}: {', '.join(missing_fields)}")

            return details

        except Exception as e:
            self.logger.error(f"Error extracting details for {service_name}: {e}")
            return None

    def retry_click(self, element, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                element.click()
                return True
            except Exception as e:
                if attempt == max_attempts - 1:
                    self.logger.error(f"Failed to click element after {max_attempts} attempts: {e}")
                    return False
                time.sleep(1)

    def navigate_back_to_services(self):
        try:

            back_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='btn btn-primary']//a[contains(text(),'Back')]"))
            )
            self.retry_click(back_button)


            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "deptCode"))
            )
            dropdown = Select(self.driver.find_element(By.ID, "deptCode"))
            dropdown.select_by_visible_text("POLICE")
 
            time.sleep(2)

        except Exception as e:
            self.logger.error(f"Error navigating back to services: {e}")
            self.handle_error_state()

    def handle_error_state(self):
        """Attempt to recover from error state by refreshing page and returning to initial state"""
        try:
            self.driver.refresh()
            time.sleep(2)
            dropdown = Select(self.driver.find_element(By.ID, "deptCode"))
            dropdown.select_by_visible_text("POLICE")
            time.sleep(2)
        except Exception as e:
            self.logger.error(f"Failed to recover from error state: {e}")

    def safe_get_text_if_exists(self, xpath, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text.strip() if element.text.strip() else "N/A"
        except (TimeoutException, NoSuchElementException):
            return "N/A"
        except Exception as e:
            self.logger.error(f"Unexpected error getting text for xpath '{xpath}': {e}")
            return "N/A"

    def save_to_json(self, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(self.services, json_file, ensure_ascii=False, indent=4)
            self.logger.info(f"Successfully saved data to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")

if __name__ == "__main__":
    url = "https://ts.meeseva.telangana.gov.in/meeseva/home.htm"
    scraper = MeesevaScraper(url)
    scraper.start()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import json

class MeesevaScraper:
    def __init__(self, url):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.url = url
        self.services = []

    def start(self):
        self.driver.get(self.url)
        self.driver.maximize_window()
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'serviceTxt')))
        self.click_cdma()  
        self.extract_service_links()
        self.save_to_json('cmda.json')
        self.driver.quit()

    def click_cdma(self):
        try:
            cdMa_link = self.driver.find_element(By.LINK_TEXT, 'CDMA')
            cdMa_link.click()
            WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, 'serDesc')))
        except Exception as e:
            print(f"An error occurred while clicking CDMA: {e}")

    def extract_service_links(self):
        try:
            services = self.driver.find_elements(By.XPATH, "//td[3]/a")
            service_count = len(services)

            for index in range(service_count):
                if(index != 1):
                    services = self.driver.find_elements(By.XPATH, "//td[3]/a")
                    service = services[index]
                    service_name = service.text
                    print(f"Processing service: {service_name}")
                    service.click()
                    WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, "(//div[@class='panel-title tCenter'])[1]")))
                    fee_label = self.safe_get_text_if_exists("(//div[@class='panel-title tCenter'])[1]") or "N/A"
                    fee_value = self.safe_get_text_if_exists("(//div[@class='labelValue tCenter'])[1]") or "N/A"
                    timeline_label = self.safe_get_text_if_exists("(//div[@class='panel-title tCenter'])[2]") or "N/A"
                    timeline_value = self.safe_get_text_if_exists("(//div[@class='labelValue tCenter'])[2]") or "N/A"

                    description = self.safe_get_text_if_exists("//td[b[text()='Description']]/following-sibling::td") or "N/A"
                    delivery_channels = self.safe_get_text_if_exists("//td[b[text()='Service Delivery Channels']]/following-sibling::td") or "N/A"
                    service_timings = self.safe_get_text_if_exists("//td[b[text()='Service Timings']]/following-sibling::td") or "N/A"
                    payment_modes = self.safe_get_text_if_exists("//td[b[text()='Service Payment Modes']]/following-sibling::td") or "N/A"

                    if all([fee_label, fee_value, timeline_label, timeline_value, description, delivery_channels, service_timings, payment_modes]):
                        service_data = {
                            'S.No': index + 1,
                            'Service Name': service_name,
                            'Fee Label': fee_label,
                            'Fee Value': fee_value,
                            'Timeline Label': timeline_label,
                            'Timeline Value': timeline_value,
                            'Description': description,
                            'Service Delivery Channels': delivery_channels,
                            'Service Timings': service_timings,
                            'Service Payment Modes': payment_modes
                        }
                        self.services.append(service_data)
                        print("Service details extracted successfully.")
                    else:
                        print(f"Missing data for service '{service_name}'. Not all required fields are present.")

                    time.sleep(2) 
            
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@class='btn btn-primary']//a[contains(text(),'Back')]"))
                    ).click()
                    print("Back button clicked")
                    time.sleep(2) 
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "deptCode"))
                    )

                    dropdown = Select(self.driver.find_element(By.ID, "deptCode"))
                    dropdown.select_by_visible_text("CDMA")
                    time.sleep(2) 

        except Exception as e:
            print(f"An error occurred while extracting service details: {e}")

    def safe_get_text_if_exists(self, xpath):
        """ Helper function to check if an element exists and get its text. """
        try:
            WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, xpath)))
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text.strip() if element.text.strip() else "N/A"
        except Exception as e:
            print(f"Element not found or not visible for xpath '{xpath}': {e}")
            return "N/A"  

    def save_to_json(self, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(self.services, json_file, ensure_ascii=False, indent=4)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"An error occurred while saving to JSON: {e}")

if __name__ == "__main__":
    url = "https://ts.meeseva.telangana.gov.in/meeseva/home.htm"
    scraper = MeesevaScraper(url)
    scraper.start()

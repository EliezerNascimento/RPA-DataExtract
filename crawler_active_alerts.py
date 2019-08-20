from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote import webelement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import os
import errno
import traceback
from configuration_reader import reader

class ActiveAlertAnalysis:
    outputPath: str()

    def __init__(self):
        """
            Main controller of all crawuling operation. 
            Whithin this method we call all methods and iterate through the plant list to get the values from 'active alerts'
            
            After each plant reading, we call our 'save' method in order to generate one output file - it's one file for each plant. 
            These file is generated even if some erro occur, so that we can track the error source and perform a bug fixing.

            Also, for each plant, we open, process & then close the web browser. 
            It is an attempt to mitigate resource consuption and also avoid memory & caching erros during our crawlling. 

            All configuration settings (user, password and url) are stored in a JSON file named "config". 
            By default, for secure reasons, it is ignored on GitHub versioning. The program does not run without this file and its configuration properly writen inside.

            JSON config file template:

            {
                "config": {
                  "url": "",
                  "user_name": "",
                  "password": "",
                  "output_path_format": ""
                }
            }

            To read above file, we use a pre built function calle "configuration_manager", which was supposed to be imported as a package,
            but for performance & learning reasons was attached to the project. 
            For more: https://github.com/leonidasnascimento/sosi.common.configuration_manager

            Args:
                self: Program reference
            
            Returns: 
                None
    
        """

        ## Getting configuration settings for site URL & Login
        confMgr = reader("config.json", "config")
        usr = confMgr.getValue("user_name")
        psw = confMgr.getValue("password")
        url = confMgr.getValue("url")
        self.outputPath = confMgr.getValue("output_path_format")

        ## Only for the first login
        driver = self.openBrowser(url)
        driver = self.login(driver, usr, psw)
        plantCount = self.getPlantCount(driver)

        # Close page
        driver.close()
        driver = None

        ## For each plant
        if (plantCount > 0):
            for index in range(plantCount):
                driver = self.openBrowser(url)
                driver = self.login(driver, usr, psw)

                lines = self.getPlantList(driver)
                line = lines[index]
                
                ## Plant name. Used to generate the output file
                plantName = line.find_elements_by_tag_name("td")[1].text + "_" + line.find_elements_by_tag_name("td")[2].text
                driver.execute_script("arguments[0].click();", line)

                ## Trying to process the crwaling. Generate the file if some error occur
                try:
                    driver = self.processActiveAlertsAndAutoSave(driver, plantName)

                    # Close page
                    driver.close()
                    driver = None

                    time.sleep(5)
                except Exception as e:
                    self.save(False, plantName, [str(e), '', '', traceback.print_exc()])
                    continue # Move on
        else:
            print("No plant to process")
        pass

    ## Open the browser in the right link.
    def openBrowser(self, url):
        """
            Open up an instance of a selected web browser and 
            directs the user to a given url.
            
            Args:
                url: Target web site
            
            Returns: 
                Object that references the open web browser
        
        """
        ## By chabging the called method you can change the web browser used on the process
        driver = webdriver.Chrome() 
        link = url
        driver.get(link)
        driver.minimize_window()

        time.sleep(5)
        return driver

    def getPlantCount(self, driver: webelement.WebElement):       
        lst = self.getPlantList(driver)
        return len(lst)
    
    ## Get the plant list
    def getPlantList(self, driver: webelement.WebElement): 
        """
            Open up an instance of a selected web browser and 
            directs the user to a given url.
            
            Args:
                url: Target web site
            
            Returns: 
                Object that references the open web browser
    
        """

        if driver is None:
            return []
        
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, 'table')))

        tablePlants = driver.find_element_by_tag_name('table')
        if tablePlants is None:
            return []

        plants = tablePlants.find_elements_by_css_selector('tr')
        if plants is None:
            return []
        else:
            return plants            
        pass
        
    # Perform login into website
    def login(self, driver: webdriver, usr : str, psw: str):
        """
            Login into a web site using a given "user name" and "password"

            Args:
                driver: Selenium Web Driver referencing the web site
                usr: User name
                psw: Password
            
            Returns:
                Logged web driver instance        
        """

        # Making sure the website (driver) is opened
        if driver is None:
            return None

        # Find "user name" field
        inputUserName = driver.find_element_by_id("username")
        if not (inputUserName is None):
            inputUserName.send_keys(usr)
        else:
            return None

        # Find "password" field
        inputPassword = driver.find_element_by_id("password")
        if not (inputPassword is None):
            inputPassword.send_keys(psw)
        else:
            return None

        # Find "login" button
        btnLogin = driver.find_element_by_class_name("btn")
        if not (btnLogin is None):
            driver.execute_script("arguments[0].click();", btnLogin)

            time.sleep(10)
            return driver
        else:
            return None

    # Process active alerts and generates one file per plant
    def processActiveAlertsAndAutoSave(self, driver: webdriver, plantName : str):
        """
        Main process for our crawling. It is a result of a empirical understanding of web page's structure.

        All needed comments on the programming logic is writen along side each programming line. It'll help on a better understanding of the process.

        Args: 
            driver: Selenium Web Driver referencing the open web site
            plantName: Plant's name that is supposed to be read

        """
        print(plantName)
        
        splitter = ';'
        active_alerts_xpath = "//*[text()='Active Alerts']"

        time.sleep(5)
        
        if driver is None:
            return []
        
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, active_alerts_xpath)))

        ## 1st. find a span with text = "Active Alerts"; then, find the "H2" elements the span is whithin; then, the header and, finally, the main "div"  
        divActiveAlerts = driver.find_element_by_xpath(active_alerts_xpath).find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..")
        if divActiveAlerts is None:
            return []

        # driver.execute_script("return arguments[0].scrollIntoView(true);", divActiveAlerts)

        spanTableHeadDescription : webelement.WebElement = divActiveAlerts.find_element_by_xpath("//*[text()='description']")
        if spanTableHeadDescription is None:
            return []

        ## Going up 8x from the 'span' element in order to find the "active alerts"
        tableActiveAlerts : webelement.WebElement = spanTableHeadDescription.find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..")
        if tableActiveAlerts is None:
            return []
        
        ## Get all rows from found table
        activeAlertsRows : webelement.WebElement = tableActiveAlerts.find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")
        if activeAlertsRows is None: 
            return []
        
        resultList = []
        for row in activeAlertsRows:
            # driver.execute_script("return arguments[0].scrollIntoView(true);", row)
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', row)

            ## Get all columns from the current row
            columns : webelement.WebElement = row.find_elements_by_tag_name("td") #note: index start from 0, 1 is col 2
            outputText = ''
            columnCounter = 0

            ## If it's a grouped row, try to expand by clicking on the #1 column (td)
            groupedItens = int(columns[1].text) if str(columns[1].text) != '' else 0 # Ternary operator
            if (len(columns) > 1) and groupedItens > 1:
                clickableTd : webelement.WebElement = columns[0]

                # Move mouse over the element. "Points the cursor" & supposedly highlights the row
                actions = ActionChains(driver)
                actions.move_to_element(clickableTd)
                actions.perform()
                
                # Click
                clickableTd.click()

                # Done. Go to the next line.
                continue

            for column in columns:
                ## We jump to the 3rd collumn because the 2 previous ones do not have required information
                columnCounter = columnCounter + 1 ## Jumping to the 3 col
                if columnCounter <= 2:
                    continue
                outputText = outputText + column.text + splitter

            resultList.append(outputText.rstrip(splitter))
        
        # Save
        self.save(True, plantName, resultList)

        return driver

    def save(self, success: bool, plantName : str, listValues: []):
        """
            Save the list of alerts into a given path by naming according to the operation status.

            If 'success = True': "OK_" will preceed the file name; otherwise "NOK_"

            Required:
                The 'outputPath' should be filled in the configuration settings reading section 

            Args:
                success: Bolean variable indicating the operation status
                plantName: Plant Name to name the file
                listValues: Active alerts from the crawling process
        """

        filename = "{}_" + str(plantName.replace(' ', '_')).lower()
        localOutputPath = self.outputPath

        if success:
            filename = filename.format('ok')
        else:
            filename = filename.format('nok')

        filename = localOutputPath.format(filename)

        # Force creation if file does not exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            for item in listValues:
                f.write("%s\n" % item)
        pass
    pass


## INITIALIZER ##
activeAlertsObj = ActiveAlertAnalysis()

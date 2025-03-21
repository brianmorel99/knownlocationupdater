# Known Location Updater
This application was designed to help update Microsoft Named Location's which can be used in Conditional Access to allow or disallow certain functions based on location.
* A Named Location is set up through Microsoft Graph API     
* Information on Named Location Setup
* * [Information from Microsoft](https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-assignment-network)
* These Named Locations can then be used in Conditional Access Policies.
* This works well for locations with a static IP, but presents problems for locations with dynamic IP.
* This application utilizes DDNS function on most routers / firewalls.


## Set up Application to Connect via Graph API
* [Microsoft Instructions for registering application](https://learn.microsoft.com/en-us/graph/auth-register-app-v2)
* Add a Name for the Application ( Named Location App)
* Choose "Accounts in this organizational directory only"
* Go to the section in the doc titled "Add credentials"
* * Choose Option 2, "Add Client Secret"
* * Make sure to save this secret as it's not displayed again.
* Save the below data from the configuration for the application
* * client_id
* * client_secret
* * tenant_id

## Add initial Named Location
* [Microsoft Instructions](https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-assignment-network)
* * Go to Identity Admin -> Conditional Access -> Name Location
* * Add an "IP Address Range"
* * * Enter a unique name to identify it.
* * * Mark as Trusted
* * * Hit the "+" button and enter the current IP address.
* * Record the below data for the coniguration of the application
* * * display_name
* * * ip_address
* * * is_trusted 
  
## Find new Named Location GUID
* Open Powershell as Administrator
* [Microsoft Instructions for Powershell Graph Application](https://learn.microsoft.com/en-us/powershell/microsoftgraph/installation?view=graph-powershell-1.0)
* * Enter the below command, and sign in to the Microsoft Tenant in the popup
* * * ```Connect-MgGraph -Scopes "Policy.Read.All"```
* * Enter the below command to install the module you need
* * * ```install-module Microsoft.Graph.Identity.SignIns```
* * Enter the below command and copy the ID for the Named Location you created.
* * * ```Get-MgIdentityConditionalAccessNamedLocation```
* * Record the below data for the coniguration of the application
* * * location_id

## Fill out your Config
* Set up a directory where you want to run the application.
* * Copy compose-sample.yml to the directory, save it as compose.yml
* Create a subdirectory & call it "config"
* * Copy config-sample.yml to config/config.yml
* You should have the below directory structure and files
```
.
 |-compose.yml
 |-config
 | |-config.yml
```
* * Open config.yml file, and fill out with the values saved earlier.
* * * The file can handle multiple locations, if not required, remove the second entry in the file.
* * Open compose.yml and fill in the environment values required for the app
* * * You can also change the default exposed port (8080) in the compose.yml file.

* A Config file is not required, and the locations can be added through the web interface.
* * It will still save a copy to the local config directory to persist the information between runs.
* * You still need the config directory, but you can leave it empty for first run

## ****** WARNING *********
* This application MUST be run behind a proxy server that handles TLS/SSL termination.
* The DDNS protocol used uses HTTP Basic Authentication, which will transmit the login information in plain text.
* Setup for a proxy server is beyond the scope of this application, Kubernetes can also be used
* Setup proxy server to terminate TLS and forward the requests to this application @ port 8080 (Unless changed)

## Run docker image
* In the directory created earlier, run the below command to run the application in the background
* * ```docker compose up -d```
* If you want to run it in the foreground, remove the "-d"
* Test the application using the below link (Unless you changed ports)
* * http://localhost:8080/admin
* * The login information was the username and password you set up in the compose.yml file.

# Build Application / Docker Image
* Install Docker
* Login to your Docker Hub account so you can push the image (Or the appropriate register)
* Run the below command to build the docker image (Replace with your username)
* * ```docker build -t [YOUR USERNAME]/knownlocationupdater .```
* * * If you want to change the image name by changing "knownlocationupdater"
* Run the below command to upload the image to the repository
* * ```docker push [YOUR USERNAME]/knownlocationupdater```

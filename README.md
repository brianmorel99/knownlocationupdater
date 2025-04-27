# Known Location Updater
This application was designed to help update Microsoft Named Location's which can be used in Conditional Access to allow or disallow certain functions based on location.

Microsoft's Conditional Access allows for controling user access to different services based on the IP address their device connects from.  This can allow for limiting a user's access to company email to only be available from a known / safe location.  The issue is that Microsoft does not provide a way to dynamically updating the ip address of the named locations.

This application uses the Microsoft Graph API to update Known Location objects with an IP address received from a Dyandmic DNS service, usually run on a firewall or router.

* Information on Named Location Setup
* * [Information from Microsoft](https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-assignment-network)


## ****** WARNING ******
* This application MUST be run behind a proxy server that handles TLS/SSL termination.
* The DDNS protocol used uses HTTP Basic Authentication, which will transmit the login information in plain text.
* Setup for a proxy server is beyond the scope of this application, Kubernetes can also be used
* Setup proxy server to terminate TLS and forward the requests to this application @ port 8080 (Unless changed)

## Quick Start / Local Test
### 1. Prepare to Run Docker Image
* Set up a directory where you want to run the application.
* * Copy compose-sample.yml to the directory, save it as compose.yml
* * * ```curl https://raw.githubusercontent.com/brianmorel99/knownlocationupdater/refs/heads/main/compose-sample.yml -o compose.yml```
* * Open compose.yml and fill in the environment values required for the app
* * * There are two sets of login information injected into the image as environment variables
* * * DDNS_USERNAME & DDNS_PASSWORD are set to the login information you will use in your DDNS configuration on the firewall
* * * ADMIN_USERNAME & ADMIN_PASSWORD are set so you can log into the web interface
* * * You can also change the default exposed port (8080) in the compose.yml file.

### 2. Create config directory
* A Config file is not required, and the locations can be added through the web interface.
* * It will still save a copy to the local config directory to persist the information between runs.
* * You still need the config directory, but you can leave it empty for first run
* Create a subdirectory & call it "config"

### 3. Run docker image
* In the directory created earlier, run the below command to run the application in the background
* * ```docker compose up -d```
* If you want to run it in the foreground, remove the "-d"
* Test the application using the below link (Unless you changed ports)
* * http://localhost:8080/admin
* * The login information was the username and password you set up in the compose.yml file.

## Project Description Video
* Please watch [This Video](https://youtu.be/kjq_ZfLiGIE) for an explanation of the project.
## Usage

### 1. Set up Application to Connect via Graph API
* [Please Follow Microsoft Instructions for registering application](https://learn.microsoft.com/en-us/graph/auth-register-app-v2)
* Add a Name for the Application (Named Location App)
* Choose "Accounts in this organizational directory only"
* Go to the section in the Microsoft guide titled "Add credentials"
* * Choose Option 2, "Add Client Secret"
* * Make sure to save this secret as it's not displayed again.
* Save the below data from the configuration for the application
* * client_id
* * client_secret
* * tenant_id

### 2. Add initial Named Location
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
  
### 3. Find new Named Location GUID
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

### 4. Prepare to Run Docker Image
* Set up a directory where you want to run the application.
* * Copy compose-sample.yml to the directory, save it as compose.yml
* * * ```curl https://raw.githubusercontent.com/brianmorel99/knownlocationupdater/refs/heads/main/compose-sample.yml -o compose.yml```
* * Open compose.yml and fill in the environment values required for the app
* * * There are two sets of login information injected into the image as environment variables
* * * DDNS_USERNAME & DDNS_PASSWORD are set to the login information you will use in your DDNS configuration on the firewall
* * * ADMIN_USERNAME & ADMIN_PASSWORD are set so you can log into the web interface
* * * You can also change the default exposed port (8080) in the compose.yml file.

### 5. Fill out your Config (Optional)
* A Config file is not required, and the locations can be added through the web interface.
* * It will still save a copy to the local config directory to persist the information between runs.
* * You still need the config directory, but you can leave it empty for first run
* Create a subdirectory & call it "config"
* * Copy config-sample.yml to config/config.yml
* * * ```curl https://raw.githubusercontent.com/brianmorel99/knownlocationupdater/refs/heads/main/config-sample.yml -o config/config.yml```
* You should have the below directory structure and files
```
.
 |-compose.yml
 |-config
 | |-config.yml
```
* * Open config.yml file, and fill out with the values saved earlier.
* * * The file can handle multiple locations, if not required, remove the second entry in the file.

### 6. Run docker image
* In the directory created earlier, run the below command to run the application in the background
* * ```docker compose up -d```
* If you want to run it in the foreground, remove the "-d"
* Test the application using the below link (Unless you changed ports)
* * http://localhost:8080/admin
* * The login information was the username and password you set up in the compose.yml file.

# Development
## Build Application / Docker Image
* Install Docker
* Login to your Docker Hub account so you can push the image (Or the appropriate register)
* Run the below command to build the docker image (Replace with your username)
* * ```docker build -t [YOUR USERNAME]/knownlocationupdater .```
* * * If you want to change the image name by changing "knownlocationupdater"
* Run the below command to upload the image to the repository
* * ```docker push [YOUR USERNAME]/knownlocationupdater```

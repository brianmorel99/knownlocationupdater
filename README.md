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
* Fill out config.yml for initial setup.
* * See sample config-sample.yml
* * Fill in the appopriate values saved earlier.


# Build Application / Docker Image
* Install Docker
* Login to your Docker Hub account so you can push the image (Or the appropriate register)
* Run the below command to build the docker image (Replace with your username)
* * ```docker build -t [YOUR USERNAME]/knownlocationupdater .```
* * * If you want to change the image name by changing "knownlocationupdater"
* Run the below command to upload the image to the repository
* * ```docker push [YOUR USERNAME]/knownlocationupdater```

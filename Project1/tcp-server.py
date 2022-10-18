from socket import *
import sys # Stop the server
import threading
import re


backlogSize = 1
serverPort = 6789
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))

serverSocket.listen() # .listen is the number of connections allowed in the queue before the socket starts to reject connections


# JSON of restricted files and directories 
restricted = { # Purpose is for O(1) lookup
    "students.html": "403 Forbidden",
    ".pgitignore": "403 Forbidden",
    ".git": "403 Forbidden", # Special case for if git directory is present, prevent access to see logs
} 

# ~~ Handler functions
def _404Handler(connectionSocket: socket):
    connectionSocket.send("HTTP/1.1 404 Not Found\n".encode())
    connectionSocket.send("Content-Type: application/json\n".encode())
    connectionSocket.send("\n\n".encode())
    serverResponse = {
        "message": "The requested resource was not found."
    }
    connectionSocket.send(str(serverResponse).encode())
    connectionSocket.close()

def _403Handler(connectionSocket: socket):
    connectionSocket.send("HTTP/1.1 403 Forbidden\n".encode())
    connectionSocket.send("Content-Type: application/json\n".encode())
    connectionSocket.send("\n\n".encode())
    serverResponse = {
        "message": "You do not have permission to access this resource."
    }
    connectionSocket.send(str(serverResponse).encode())
    connectionSocket.close()

def _400Handler(connectionSocket: socket):
    connectionSocket.send("HTTP/1.1 400 Bad Request\n".encode())
    connectionSocket.send("Content-Type: application/json\n".encode())
    connectionSocket.send("\n\n".encode())
    serverResponse = {
        "message": "Malformed request."
    }
    connectionSocket.send(str(serverResponse).encode())
    connectionSocket.close()

# Entry point, messaage == "/"
def entry(connectionSocket: socket):
    connectionSocket.send("HTTP/1.1 200 OK\n".encode())
    connectionSocket.send("Content-Type: application/json\n".encode())
    connectionSocket.send("\n\n".encode())
    serverResponse = {
        "message": "Ok!"
    }
    connectionSocket.send(str(serverResponse).encode()) # First convert the JSON data into string and then encode
    connectionSocket.close()

# Function that handles the return of HTML files
def htmlResponse(connectionSocket: socket, htmlCode: str):
    connectionSocket.send("HTTP/1.1 200 OK\n".encode()) 
    connectionSocket.send("Content-Type: text/html\n".encode())
    connectionSocket.send("\n\n".encode())
    connectionSocket.send(htmlCode.encode())
    connectionSocket.close()

def plainTextResponse(connectionSocket: socket, text: str):
    connectionSocket.send("HTTP/1.1 200 OK\n".encode())
    connectionSocket.send("Content-Type: text/plain\n".encode())
    connectionSocket.send("\n\n".encode())
    connectionSocket.send(text.encode())
    connectionSocket.close()

def cssTextResponse(connectionSocket: socket, text: str):
    connectionSocket.send("HTTP/1.1 304 Not Modified\n".encode())
    connectionSocket.send("Content-Type: text/css".encode())


# ~~ ## 

# ~~ Utility functions
# Checks if the requested resource is restricted
def checkForbidden(path: str):
    isRestricted = restricted.get(path) # Returns None if restricted
    if isRestricted != None: 
        return True
    fileExtension = getFileExtension(path) # Returns None if directory
    if fileExtension == None: # If the file extension is None, then it is a directory
        return True
    elif fileExtension == "py": # Do not display py files
        return True 
    return False


# Returns the file extension
def getFileExtension(filename: str) -> str or None:
    # Get the index of the last dot
    lastDotIndex = filename.rfind(".")
    # If not found
    if lastDotIndex == -1: 
        return None
    extension = filename[lastDotIndex + 1:]
    return extension
    

# ~~ ##


# Process request function
def processRequest(connectionSocket: socket):
    try:
        message = connectionSocket.recv(1024).decode() # Decode the request 
        requestData = message.split() # Split the request into a list

        if len(requestData) == 0: # If the request is empty, return 400 to indicate a bad request
            _400Handler(connectionSocket) 
            return
        
        filename = requestData[1] # Read the resource requested
        filename = filename.lower() # Convert filename to all lowercase
        # The reason for lowercasing the filename is if the system open function is case insensitive

        if filename == "/": # Check if at entry/root (http://127.0.0.1:6789/)
            entry(connectionSocket) 
            return 

        # Filename sanitization

        # Use regular expressions to remove trailing slashes
        filename = re.sub(r'\/+$', "", filename) # Remove trailing slashes
        # This can be used to access: http://127.0.0.1:6789/HelloWorld.html//// 
        requestedFile = filename.split("/")[-1] # Get the name of the file
        # So that we can do a lookup for the restricted file and omit the directory
        # Example: http://127.0.0.1:6789/grades////students.html bypasses the restricted file lookup


        if checkForbidden(requestedFile): # Checks if requested resource is forbidden. Includes: directories and files with .py extension
            _403Handler(connectionSocket) # Note: 403 will be returned if a file extension was not provided
            return

        # Open the file
        file = open("." + filename, "r") # For security purposes, open the file in read mode only using a second argument "r" 
        # Get the name of the file
        outputdata = file.read() # Reads the file and returns a string

        if len(outputdata) == 0: # If the file is empty, return 404
            raise IOError # IO Error, file does not exist
        
        # Send the data
        fileExt = getFileExtension(filename)
        if fileExt == "html":
            htmlResponse(connectionSocket, outputdata)
        else:
            plainTextResponse(connectionSocket, outputdata)
    
    except IOError:
        _404Handler(connectionSocket)
    connectionSocket.close() # Close the connection

while True:
    print("Ready to serve..")
    clientSocket, addr = serverSocket.accept() # Method is a blocking call, it waits until a client connects
    clientConnectionThread = threading.Thread(target = processRequest, args = (clientSocket,)) # Create a new thread to handle the client
    clientConnectionThread.start() # Start the new thread


serverSocket.close()
sys.exit()

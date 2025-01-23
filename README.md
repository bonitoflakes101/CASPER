# CASPER Project Setup

## **Setup Instructions**

### **1. Fork the Repository**
- Go to the GitHub repository and click the **Fork** button to create a copy of the repository in your GitHub account.

### **2. Clone the Repository**
- Go to your GitHub account and open the forked repository.
- Click the **Code** button and copy the repository URL (either HTTPS or SSH).
- Clone the repository to your local machine by running the following command and pasting the repository URL in your terminal:
  ```bash
  git clone https://github.com/YOUR_USERNAME/CASPER.git

### **3. Change to the Project Directory**:
  ```bash
    cd CASPER
```

### **4. Create and Activate Virtual Environment**:
- Inside the project directory, create a virtual environment using the following command:
    ```bash
    python -m venv caspervenv
    ```
- Activate Virtual Environment
   ```bash
    caspervenv\Scripts\activate
    ```

### **5. Install Flask**:
  ``` bash
    pip install flask
  ```

### **6.Run the Application**:
  ``` bash
    python main.py
  ```

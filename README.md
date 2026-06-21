# Ultrasound Image Converter

## Requirements

* Python 3.10+
* Java 17+

## Running the client

1. Go to the directory:

```
cd client
```

2. Create a virtual environment:

```
python3 -m venv .venv
```

3. Activate the environment:

* Linux / WSL / Mac:

```
source .venv/bin/activate
```

* Windows:

```
.venv\Scripts\activate
```

4. Install dependencies:

```
pip install -r requirements.txt
```

5. Config the client in constants.py

6. Run the client:

```
python3 main.py
```

## Running the Python Server

1. Go to the directory:

```
cd server-python
```

2. Create a virtual environment:

```
python3 -m venv .venv
```

3. Activate the environment:

* Linux / WSL / Mac:

```
source .venv/bin/activate
```

* Windows:

```
.venv\Scripts\activate
```

4. Install dependencies:

```
pip install -r requirements.txt
```

5. Run the server:

```
python3 main.py
```

## Running the Java Server

### Option 1 — Run using Maven (recommended for development)
Replace \<num\> with the size of your computer's RAM memory * 0.9 (round down to the nearest integer)

```
cd server-java
./mvnw spring-boot:run -Dspring-boot.run.jvmArguments="-Xmx<num>g"
```

### Option 2 — Run using the generated JAR

1. Build the project:

```
cd server-java
./mvnw clean package
```

2. Run the JAR:  
Replace \<num\> with the size of your computer's RAM memory * 0.9 (round down to the nearest integer)

```
java -Xmx<num>g -jar target/converter-0.0.1-SNAPSHOT.jar
```


## Notes

* If you are going to use `git clone` command, you need to have Git LFS installed to obtain the CSV files
* Make sure `JAVA_HOME` is configured if using Maven
* Always activate the Python virtual environment before running the server
* Do not commit `.venv/` or `target/` directories

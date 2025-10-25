@ECHO OFF
SET DIR=%~dp0
SET WRAPPER_JAR=%DIR%gradle\wrapper\gradle-wrapper.jar

IF EXIST "%WRAPPER_JAR%" (
  IF NOT DEFINED JAVA_HOME (
    SET JAVA_CMD=java
  ) ELSE (
    SET JAVA_CMD="%JAVA_HOME%\bin\java.exe"
  )
  %JAVA_CMD% -Xmx64m -Xms64m -classpath "%WRAPPER_JAR%" org.gradle.wrapper.GradleWrapperMain %*
  EXIT /B %ERRORLEVEL%
)

ECHO Gradle wrapper JAR not found. Install Gradle 8.7+ and run "gradle wrapper" inside the android\ directory to generate the wrapper files.>&2
WHERE gradle >NUL 2>&1
IF %ERRORLEVEL% EQU 0 (
  gradle %*
  EXIT /B %ERRORLEVEL%
)
EXIT /B 1

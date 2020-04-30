pipeline {
    agent { label 'django-slave' }
    options { disableConcurrentBuilds() }
    stages {
        stage('Build') {
            steps {
                sh 'chmod 777 ${WORKSPACE}/build_scripts/build_script.py'
				sh "python3 ${WORKSPACE}/build_scripts/build_script.py"
            }
        }
    }
}
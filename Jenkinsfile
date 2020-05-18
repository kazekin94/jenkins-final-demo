pipeline {
    agent { label 'django-slave' }
    options { disableConcurrentBuilds() }
    stages {
        stage('Build') {
            steps {
                sh 'chmod 777 ${WORKSPACE}/build_scripts/build_script.py'
				sh "sudo python3 ${WORKSPACE}/build_scripts/build_script.py"
            }
        }
        stage('Copy Artifacts') {
            steps {
                sh 'chmod 777 ${WORKSPACE}/build_scripts/copy_artifacts.py'
			    sh "sudo python3 ${WORKSPACE}/build_scripts/copy_artifacts.py"
            }
        }
        stage('Deploy') {
            steps {
                sh 'chmod 777 ${WORKSPACE}/build_scripts/deploy-colud-native.py'
			    sh "sudo python3 ${WORKSPACE}/build_scripts/deploy-colud-native.py"
            }
        }
    }
}
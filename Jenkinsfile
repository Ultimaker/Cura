parallel_nodes(['linux && cura', 'windows && cura']) {
    timeout(time: 2, unit: "HOURS") {

        // Prepare building
        stage('Prepare') {
            // Ensure we start with a clean build directory.
            step([$class: 'WsCleanup'])

            // Checkout whatever sources are linked to this pipeline.
            checkout scm
        }

        // If any error occurs during building, we want to catch it and continue with the "finale" stage.
        catchError {
            stage('Pre Checks') {
                if (isUnix()) {
                    // Check shortcut keys
                    try {
                        sh """
                            echo 'Check for duplicate shortcut keys in all translation files.'
                            ${env.CURA_ENVIRONMENT_PATH}/master/bin/python3 scripts/check_shortcut_keys.py
                        """
                    } catch(e) {
                        currentBuild.result = "UNSTABLE"
                    }

                    // Check setting visibilities
                    try {
                        sh """
                            echo 'Check for duplicate shortcut keys in all translation files.'
                            ${env.CURA_ENVIRONMENT_PATH}/master/bin/python3 scripts/check_setting_visibility.py
                        """
                    } catch(e) {
                        currentBuild.result = "UNSTABLE"
                    }
                }
            }

            // Building and testing should happen in a subdirectory.
            dir('build') {
                // Perform the "build". Since Uranium is Python code, this basically only ensures CMake is setup.
                stage('Build') {
                    def branch = env.BRANCH_NAME
                    if(!fileExists("${env.CURA_ENVIRONMENT_PATH}/${branch}")) {
                        branch = "master"
                    }

                    // Ensure CMake is setup. Note that since this is Python code we do not really "build" it.
                    def uranium_dir = get_workspace_dir("Ultimaker/Uranium/${branch}")
                    cmake("..", "-DCMAKE_PREFIX_PATH=\"${env.CURA_ENVIRONMENT_PATH}/${branch}\" -DCMAKE_BUILD_TYPE=Release -DURANIUM_DIR=\"${uranium_dir}\"")
                }

                // Try and run the unit tests. If this stage fails, we consider the build to be "unstable".
                stage('Unit Test') {
                    if (isUnix()) {
                        // For Linux to show everything
                        def branch = env.BRANCH_NAME
                        if(!fileExists("${env.CURA_ENVIRONMENT_PATH}/${branch}")) {
                            branch = "master"
                        }
                        def uranium_dir = get_workspace_dir("Ultimaker/Uranium/${branch}")

                        try {
                            sh """
                                cd ..
                                export PYTHONPATH=.:"${uranium_dir}"
                                ${env.CURA_ENVIRONMENT_PATH}/${branch}/bin/pytest -x --verbose --full-trace --capture=no ./tests
                            """
                        } catch(e) {
                            currentBuild.result = "UNSTABLE"
                        }
                    }
                    else {
                        // For Windows
                        try {
                            // This also does code style checks.
                            bat 'ctest -V'
                        } catch(e) {
                            currentBuild.result = "UNSTABLE"
                        }
                    }
                }

                stage('Code Style') {
                    if (isUnix()) {
                        // For Linux to show everything
                        def branch = env.BRANCH_NAME
                        if(!fileExists("${env.CURA_ENVIRONMENT_PATH}/${branch}")) {
                            branch = "master"
                        }
                        def uranium_dir = get_workspace_dir("Ultimaker/Uranium/${branch}")

                        try {
                            sh """
                                cd ..
                                export PYTHONPATH=.:"${uranium_dir}"
                                ${env.CURA_ENVIRONMENT_PATH}/${branch}/bin/python3 run_mypy.py
                            """
                        } catch(e) {
                            currentBuild.result = "UNSTABLE"
                        }
                    }
                }
            }
        }

        // Perform any post-build actions like notification and publishing of unit tests.
        stage('Finalize') {
            // Publish the test results to Jenkins.
            junit allowEmptyResults: true, testResults: 'build/junit*.xml'

            notify_build_result(env.CURA_EMAIL_RECIPIENTS, '#cura-dev', ['master', '2.'])
        }
    }
}

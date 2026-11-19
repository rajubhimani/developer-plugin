plugins {
    application
    alias(libs.plugins.spotless)
}

group = "{{javagroup}}"
version = "0.1.0"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(<java-version>)
    }
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testRuntimeOnly(libs.junit.platform.launcher)
}

application {
    mainClass = "{{javapkg}}.Main"
}

tasks.withType<JavaCompile>().configureEach {
    options.encoding = "UTF-8"
    options.release = <java-version>
    // Every warning, deprecated calls included, fails the build.
    options.compilerArgs.addAll(listOf("-Xlint:all", "-Werror"))
}

tasks.test {
    useJUnitPlatform()
}

spotless {
    java {
        target("src/**/*.java")
        googleJavaFormat(libs.versions.google.java.format.get())
    }
}

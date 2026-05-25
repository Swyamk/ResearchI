# NutriMind Mobile – Flutter
FROM ghcr.io/cirruslabs/flutter:stable AS builder
WORKDIR /app
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get
COPY . .
ARG API_BASE_URL=http://backend:8000/api/v1
RUN flutter build apk --release --dart-define=API_BASE_URL=$API_BASE_URL

# Export the APK
FROM alpine:3.19
COPY --from=builder /app/build/app/outputs/flutter-apk/app-release.apk /output/nutrimind.apk
CMD ["sh", "-c", "echo 'APK available at /output/nutrimind.apk'"]

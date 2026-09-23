FROM nginx:alpine

# Copy custom frontend into Nginx default web root with root ownership and 755 permissions per SonarQube rule
COPY --chown=root:root --chmod=755 index.html /usr/share/nginx/html/index.html

EXPOSE 80

FROM nginx:alpine

# Copy custom frontend into Nginx default web root with root ownership and 755 permissions per SonarQube rule
COPY --chown=root:root --chmod=755 index.html /usr/share/nginx/html/index.html

# Setup permissions for non-root nginx user and grant capability to bind port 80
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx && \
    apk add --no-cache libcap && \
    setcap 'cap_net_bind_service=+ep' /usr/sbin/nginx

# Run as non-root user to satisfy container security rules
USER nginx

EXPOSE 80

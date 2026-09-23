FROM nginx:alpine

# Configure Nginx to run in single-process mode (bypasses socketpair restriction on hypervisors)
RUN sed -i '1i master_process off;' /etc/nginx/nginx.conf

# Copy custom frontend into Nginx default web root
COPY index.html /usr/share/nginx/html/index.html
COPY preview.html /usr/share/nginx/html/preview.html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

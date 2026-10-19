FROM nginx:alpine

# Szablon – nginx przy starcie podstawia ${BACKEND_URL} ze zmiennej środowiskowej
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY public/ /usr/share/nginx/html/

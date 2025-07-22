.PHONY: dev backend frontend

backend:
	cd backend && python manage.py runserver

frontend:
	cd frontend-ui && npm run start:dev

dev:
	(cd backend && python manage.py runserver) & \
	(cd frontend-ui && npm run start:dev) & \
wait

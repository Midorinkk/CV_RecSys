IMAGE := resume_app

build:
	@docker-compose build

init-db:
	@docker-compose run --rm app python app/init_db.py

run: build init-db
	@docker-compose up

down:
	@docker-compose down

logs:
	@docker-compose logs -f

docker::run { 'imagebank':
  image   => 'imagebank',
  ports           => '8000:8000',
  env            => ["DB_ENGINE=django.db.backends.sqlite3",
                     "DB_NAME=db.sqlite3",
                    "DJANGO_MANAGEPY_MIGRATE=on",
                    "DJANGO_MANAGEPY_INITADMIN=on",
                    ],
}
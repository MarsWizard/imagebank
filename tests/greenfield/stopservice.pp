# docker_compose { '/greedfield/docker-compose.yml':
#   #compose_files => ['/greedfield/docker-compose.yml'],
#   ensure  => 'absent',
# }

docker::run { 'imagebank':
  image   => 'imagebank',
  ensure  => absent,
}
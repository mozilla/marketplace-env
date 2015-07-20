# This builds every image, tags it as latest and then pushes it up to docker hub.

baseimages=(mysql nodejs phantomjs python27)
for i in "${baseimages[@]}"
do
    echo 'Building and pushing' $i
    docker build -t mozillamarketplace/centos-$i-mkt:latest docker/base-images/$i
    docker push mozillamarketplace/centos-$i-mkt:latest
    echo '... done.'
done

images=(mysql-service mysql-data nginx elasticsearch redis memcached)
for i in "${images[@]}"
do
    echo 'Building and pushing' $i
    docker build -t mozillamarketplace/$i:latest mkt/data/images/$i
    docker push mozillamarketplace/$i:latest
    echo '... done.'
done

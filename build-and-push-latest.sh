# This builds every image, tags it as latest and then pushes it up to docker hub.

baseimages=(mysql python27)
for i in "${baseimages[@]}"
do
    echo 'Building and pushing' $i
    docker build -t mozillamarketplace/centos-$i-mkt:latest docker/base-images/$i
    docker push mozillamarketplace/centos-$i-mkt:latest
    echo '... done.'
done

mkdir ~/.dti
BASEDIR=$(dirname "$0")
cp -rf $BASEDIR/main.py ~/.dti/main.py
cp -rf $BASEDIR/dti.py ~/.dti/dti.py
cp -rf $BASEDIR/visual.py ~/.dti/visual.py
touch ~/Desktop/DTI_PIPELINE
> ~/Desktop/DTI_PIPELINE
echo "python3 ~/.dti/main.py" >> ~/Desktop/DTI_PIPELINE
chmod u+x ~/Desktop/DTI_PIPELINE
echo "FINISHED INSTALLATION"
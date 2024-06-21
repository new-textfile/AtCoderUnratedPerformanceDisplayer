#!/bin/bash
DATE=`date '+%Y-%m-%d %H:%M:%S'`
logfile="$ACUPDDIR/logs/templog"
updater_folder="$ACUPDDIR/updater"
acupd_perfs_folder="$ACUPDDIR/data/AtCoderUnratedPerformances"
acupd_acresults_folder="$ACUPDDIR/data/AtCoderContestResults"
updater_perfs_folder="$updater_folder/tempdata/AtCoderUnratedPerformances"
updater_acresults_folder="$updater_folder/tempdata/AtCoderContestResults"

set -e

echo "" > $logfile

if [ -e $updater_folder/tempdata/added_contest_name ]; then
    rm $updater_folder/tempdata/added_contest_name
fi

cd $updater_folder/src
python3 $updater_folder/src/main.py >> $logfile 2>&1
contest_name=$(cat $updater_folder/tempdata/added_contest_name )
echo "[`date`]<$contest_name> main finished" >> $logfile

rm $acupd_perfs_folder/userperfs -r >> $logfile 2>&1
echo "[`date`]<$contest_name> remove userperfs finished" >> $logfile 
cp $updater_perfs_folder/userperfs $acupd_perfs_folder/ -r >> $logfile 2>&1
echo "[`date`]<$contest_name> copy userperfs finished" >> $logfile
cd $acupd_perfs_folder
git add . >> $logfile 2>&1
echo "[`date`]<$contest_name> git add finished" >> $logfile
git commit -m "update userperfs("$contest_name")" >> $logfile 2>&1
echo "[`date`]<$contest_name> git commit finished" >> $logfile
git push git@github.com:new-textfile/AtCoderUnratedPerformances.git >> $logfile 2>&1
echo "[`date`]<$contest_name> git push finished" >> $logfile

rm $acupd_acresults_folder/default_aperfs.json  >> $logfile 2>&1
rm $acupd_acresults_folder/fetched_contests.json  >> $logfile 2>&1
rm $acupd_acresults_folder/fetched_contests_info.json  >> $logfile 2>&1
echo "[`date`]<$contest_name> remove ac_contest_results files finished" >> $logfile
rm $acupd_acresults_folder/results -r  >> $logfile 2>&1
echo "[`date`]<$contest_name> remove results finished" >> $logfile
rm $acupd_acresults_folder/useraperfs -r  >> $logfile 2>&1
echo "[`date`]<$contest_name> remove useraperfs finished" >> $logfile
rm $acupd_acresults_folder/userinnerperfs -r  >> $logfile 2>&1
echo "[`date`]<$contest_name> remove_userinnerperfs finished" >> $logfile
cp $updater_acresults_folder/default_aperfs.json $acupd_acresults_folder  >> $logfile 2>&1 
cp $updater_acresults_folder/fetched_contests.json $acupd_acresults_folder  >> $logfile 2>&1
cp $updater_acresults_folder/fetched_contests_info.json $acupd_acresults_folder  >> $logfile 2>&1
echo "[`date`]<$contest_name> copy ac_contest_results files finished" >> $logfile
cp $updater_acresults_folder/results $acupd_acresults_folder -r >> $logfile 2>&1
echo "[`date`]<$contest_name> copy results finished" >> $logfile
cp $updater_acresults_folder/useraperfs $acupd_acresults_folder -r >> $logfile 2>&1
echo "[`date`]<$contest_name> copy useraperfs finished" >> $logfile
cp $updater_acresults_folder/userinnerperfs $acupd_acresults_folder -r >> $logfile 2>&1
echo "[`date`]<$contest_name> copy userinnerperfs finished" >> $logfile
cd $acupd_acresults_folder
git add . >> $logfile 2>&1
echo "[`date`]<$contest_name> git add finished finished" >> $logfile
git commit -m "update useraperfs and userinnerperfs("$contest_name")" >> $logfile 2>&1
echo "[`date`]<$contest_name> git commit finished" >> $logfile
git push git@github.com:new-textfile/AtCoderContestResults.git >> $logfile 2>&1
echo "[`date`]<$contest_name> git push finished" >> $logfile
mv "$logfile" "$ACUPDDIR/logs/$contest_name.log"

exit 0

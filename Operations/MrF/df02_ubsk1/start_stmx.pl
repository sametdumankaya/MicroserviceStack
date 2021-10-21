#!/usr/bin/perl
$options{localhg} = "/home/hmlatapie/hg";
$options{inputQuoteStream} = "/home/hmlatapie/stmxdata/ls_archive/livestream_20201009";
$options{outputQuoteStream} = "/tmp/simoutput001";
`rm $options{outputQuoteStream}`;
`touch $options{outputQuoteStream}`;
$datacmd = "";
$datadir = shift;

$inputQuoteStream = "-v $options{inputQuoteStream}:/home/hmlatapie/stmxdata/simulator/siminput";

$outputQuoteStream = "-v $options{outputQuoteStream}:/home/hmlatapie/stmxdata/simulator/simoutput";

$datacmd = "-v $datadir:/data"
	if $datadir;

$localhg = "-v $options{localhg}:/hg"
	if $options{localhg};
	
$tiddlywiki = "-p $options{tiddlywikiport}:8080"
	if $options{tiddlywikiport};

$options{tiddlywikiname} = 'adhoc'
	if !$options{tiddlywikiname};

$tiddlywikiname = "-e TIDDLYWIKINAME=$options{tiddlywikiname}"
	if $options{tiddlywikiname};

$etherpad = "-p $options{etherpadport}:9001"
	if $options{etherpadport};

$options{name} = "stmx";
$options{imagename} = "stmxnew";
`sudo docker rm -f $options{name}`;
`sudo docker run --env PARENT_HOSTNAME=\$(hostname) --name $options{name} --hostname $options{name} $inputQuoteStream $outputQuoteStream $datacmd -d --link bb_mysql --link redistimeseries $localhg $options{imagename} /bin/bash -c \"sleep 10 && delta.pl start _delta\"`;
#`sudo docker run --env PARENT_HOSTNAME=\$(hostname) --name $options{name} --hostname $options{name} $datacmd -d --link bb_mysql --link redis --link redistimeseries $localhg $tiddlywiki $tiddlywikiname $etherpad $options{imagename} /bin/bash -c \"sleep 10 && delta.pl start _delta $startservices\"`;

`stmx.pl exec ctwCentaurTrading.pl startSimMode`;

$datacmdmsg = "with $datacmd"
	if $datacmd;
print "$options{imagename} started as $options{name} with data at:$datacmdmsg\n";

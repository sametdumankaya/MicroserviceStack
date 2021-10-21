#!/usr/bin/perl
use Data::Dumper;
use Carp;
use Time::HiRes qw(time sleep);
use Getopt::Long;

$redisDBs = "/home/hmlatapie/stmxdata/redis/tradinglive";
$usage = <<EOS;
$0 cmd options
   valid commands:
      redisGetDates
      redisStart date, port
      redisStartAll startingPort maxPortCount
      createReversePortForward startingPort maxPortCount
      redisKill date
      streamCreate date
   options:
EOS

GetOptions(
   'stringparam=s' => \$options{stringparam},
   'booleanparam' => \$options{booleanparam}
   );

confess $usage
   if !@ARGV;

$command = shift;

if($command eq 'redisGetDates')
{
   @files = glob("$redisDBs/*"); 
	for $file (@files)
	{
		$file =~ /dump_(\d{8})/;
		$filesize = -s $file;
		$filesize = $filesize / 1000000000;
		$date = $1;
		next
			if $filesize < .5;
		$filesize = sprintf("%.3fG", $filesize);
		print "$date,$filesize\n";
	}
}
elsif($command eq 'redisStart')
{
	$date = shift;
	$port = shift;
	confess $usage
		if !$date || !$port;

	print "attempting to fire up a redis server for date: $date on port: $port\n";
   @files = glob("$redisDBs/*$date*"); 
	confess "more than one choice for given date... please fix"
		if @files > 1;
	confess "no matching databases for given date... please fix"
		if @files == 0;

	$filepath = $files[0];
	print "filepath: $filepath\n";
	$filepath =~ /^(.*)\/(.*)$/;
	$filename = $2;
	print "filename: $filename\n";
	#$dstfilepath = "/tmp/$filename";

	$dstfilepath = $filepath;
	#`sudo rm $dstfilepath`;
	#`cp $filepath $dstfilepath`;
	print "processing: $dstfilepath\n";

	#$homedir = "/home/hmlatapie/stmxdata/redis";
	#$homedir = "/tmp";
	$homedir = $redisDBs;
   chdir $homedir;
	$containername = "mrfBacktestFullPort$port";

   print `sudo docker rm -f $containername`;
   $cmd = <<"EOS";
sudo docker run -d -p $port:6379 -v $dstfilepath:/data/dump.rdb --name $containername redislabs/redistimeseries
EOS
   print `$cmd`;
}
elsif($command eq 'redisStartAll')
{
	my $startingPort = shift;
	my $maxPortCount = shift;
   
	confess $usage
		if !$startingPort || !$maxPortCount;

	$dates = getDateList();
	@dates = @$dates;
	$curPort = $startingPort;
	$curDate = 0;
	$curContainerNumber = 0;
	for $date (@dates)
	{
		print "starting servier date: $dates[$curDate] port: $curPort\n";
		print `./mrf_DFin.pl redisStart $dates[$curDate] $curPort`; 
		++$curDate; ++$curPort; ++$curContainerNumber;
		last 
		   if $curContainerNumber >= $maxPortCount;
	}
}
elsif($command eq 'createReversePortForward')
{
   $startingPort = shift;
	$maxPortCount = shift;
	confess $usage
	   if !$startingPort || !$maxPortCount;

	$sshcmd = "ssh ";
	for($curPort = $startingPort;$curPort < ($startingPort + $maxPortCount); ++$curPort)
	{
		$sshcmd .= " -R$curPort:localhost:$curPort ";
	}
	$sshcmd .= " df03_ubsk3";
	$sshcmd = "while true; do $sshcmd ; done";
	print "$sshcmd\n";
}
elsif($command eq 'streamCreate')
{
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
}
else
{
   confess $usage;
}

sub getDateList
{
   my @files = glob("$redisDBs/*"); 
	my (@dates,$file,$filesize,$date);

	for $file (@files)
	{
		$file =~ /dump_(\d{8})/;
		$filesize = -s $file;
		$filesize = $filesize / 1000000000;
		$date = $1;
		next
			if $filesize < .5;
		push @dates, $date;
	}
	return \@dates;
}


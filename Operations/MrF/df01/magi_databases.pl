#!/usr/bin/perl
use Data::Dumper;
use Carp;
use Time::HiRes qw(time sleep);
use Getopt::Long;

$usage = <<EOS;
$0 cmd options
   valid commands:
      restore_redis
      remove_redis
   options:
EOS

GetOptions(
   'stringparam=s' => \$options{stringparam},
   'booleanparam' => \$options{booleanparam}
   );

confess $usage
   if !@ARGV;

$command = shift;

if($command eq 'remove_redis')
{
	print `sudo docker rm -f redismagi_mind`;
	print `sudo docker rm -f redis`;
	print `sudo docker rm -f redistimeseries`;
	print `sudo docker rm -f redismagi`;
}
elsif($command eq 'restore_redis')
{
	my $cmd=<<'EOS';
sudo docker run -d -p 6378:6379 -v $(pwd)/redismagi_mind:/data --name redismagi_mind redislabs/redistimeseries
EOS
	print `$cmd`;
	#sudo docker run -d -p 6379:6379 -v $(pwd)/redis.rdb:/data/dump.rdb –-name redis redislabs/redistimeseries
	my $cmd=<<'EOS';
sudo docker run -d -p 6379:6379 -v $(pwd)/redis:/data --name redis redislabs/redistimeseries
EOS
	print `$cmd`;
	#sudo docker run -d -p 6380:6379 -v $(pwd)/redistimeseries.rdb:/data/dump.rdb –-name redistimeseries redislabs/redistimeseries
	my $cmd=<<'EOS';
sudo docker run -d -p 6380:6379 -v $(pwd)/redistimeseries:/data --name redistimeseries redislabs/redistimeseries
EOS
	print `$cmd`;
	#sudo docker run -d -p 6381:6379 -v $(pwd)/redismagi.rdb:/data/dump.rdb –-name redismagi redislabs/redistimeseries
	my $cmd= <<'EOS';
sudo docker run -d -p 6381:6379 -v $(pwd)/redismagi:/data --name redismagi redislabs/redistimeseries
EOS
	print `$cmd`;
}
else
{
   confess $usage;
}



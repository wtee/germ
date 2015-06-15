#!/usr/pkg/bin/perl 

# germ- let your ideas germinate.
# (c) 2009--11, Wesley Teal, wt@sdf.lonestar.org
# includes code and comments by slugmax@sdf.lonestar.org
#
# distributed under the MIT/X Consortium License, see LICENSE for details

use warnings;
use strict;
use Text::Wrap;
$Text::Wrap::columns=65;
use Fcntl qw(:flock);
use POSIX qw(strftime);

# Nix the PATH and prevent SETUID/SETGID
$ENV{PATH} = "";
$> = $<;
$) = $(;

# === Configurable Variables ===

# The directory used in gopher links, make sure not to end with a "/"
my $base_dir ="/users/USERNAME";

# Full path name to the directory you store your *.post, header.txt, and div.txt
# files in.  Make sure not to end with a "/"
my $dir = "/ftp/pub$base_dir/dat";

# The maximum number of posts you want displayed per phlog page
my $max_posts = 6;

# Permalink text. Shown as a link to individual posts.  It's a good idea to have
# this end with something about comments so that the comment count isn't just a
# random-seeming number sitting next to this link
my $permalink_text = "View Post/Comments";

# This is the text that will be displayed on the main page when you use the
# "--more--" tag in your posts.
my $more_text = "[Continued...]";

# This is printed after every comment that is left on your gopherlog.  Changing 
# this after you have comments will mess up comment counts, so it's best to 
# change it right away or not at all.  This also divides tags from posts.
my $cmt_div = "---";

# This scripts name, so it can get all self-referential
my $name = "germ.cgi";

# The server that is hosting the script
my $server = "sdf.lonestar.org";

# The port number the server uses; don't change this unless you know its serving
# from a different port
my $port = 70;

# === End Configurable Variables ===

my $txt_string = "\tnull\ttext\t70";
my $ver = "germ 0.4.0";
my $header = "header.txt";
my $div = "div.txt";
my $footer = "i$txt_string\r\nipowered by $ver$txt_string\r\n.\r\n";
my $com_string = "\t$base_dir/$name\t$server\t$port";
my @tag_list;

# check to see if the server is using cgi variables to communicate with germ
# or if its passing information as arguments like Bucktooth 
my $query;

if (exists $ENV{QUERY_STRING}) {
    $query = $ENV{QUERY_STRING};
} else {
    $query = join(' ',@ARGV);
}

#get posts
opendir(DH, $dir) || die "3Can't open $dir. $! \r\n";
my @posts = grep(/post$/, readdir(DH));
closedir(DH);
@posts = sort { -M "$dir/$a" <=> -M "$dir/$b" } @posts;

#print main page
if (length($query) == 0) {
    if (($max_posts - 1) > $#posts) {
        $max_posts = $#posts + 1;
    }
    &print_page (@posts[0 .. ($max_posts - 1)]);
    if ($#posts > ($max_posts - 1)) {
        print "1Older Posts\t$base_dir/$name?archive1\t$server\t$port\r\n";
    }

# show individual posts/comments
} elsif ($query =~ /^\w+\.post$/) {      
    my $go_string = "\t$base_dir/$name?$query\t$server\t$port";
    my $post = "$query";
    my $cmt = "$post.cmt";
    &print_file ($header);
    &print_file ($div);
    print "1Back to Main Page$com_string\r\n";
    print "i$txt_string\r\n";
    my $date = strftime ("%Y %B %d, %R", localtime((stat ("$dir/$post"))[9]));

    print "i$date$txt_string\r\n";
    print "i$txt_string\r\n";
    &print_file ($post);
    print "i$txt_string\r\n";
    print "7Leave Comment$com_string\r\n";
    $Text::Wrap::separator = "$txt_string\r\n";
    print wrap("i", "i", "To leave comment enter \"$post\" at the prompt followed by a space and then your comment of 950 characters or less."), "$txt_string\r\n";
    $Text::Wrap::separator = "\n";
    if ($tag_list[0]) {
        &print_tags (@tag_list);
    }
    &print_file ($div);
    if (-e "$dir/$cmt") {
        &print_file ("$cmt");
    }

#show archives
} elsif ($query =~ /^archive\d+$/) {    
    my $num = $query;
    $num  =~ s/archive//;
    my $min = $max_posts * $num;
    my $max = $max_posts * $num + $max_posts - 1;
    if ($max > $#posts) {
        $max = $#posts;
    }
    &print_page (@posts[$min .. $max]);
    if ($num == 1) {
        print "1Newer Posts\t$base_dir/$name\t$server\t$port\r\n";
    }elsif ($num > 1) {
        my $prev_page = $num - 1;
        print "1Newer Posts\t$base_dir/$name?archive$prev_page\t$server\t$port\r\n";
    }
    if ($#posts > $max) {
        $num += 1;
        print "1Older Posts\t$base_dir/$name?archive$num\t$server\t$port\r\n";
    }
    
#show files containing a specific tag
} elsif ($query =~ /^tag=(\w+)/) {
    my $tag = $query;
    my @tag_files;
    $tag =~ s/^tag=//;
    $tag =~ s/_/ /g;
    foreach my $file (@posts) {
        open (FH, "< $dir/$file") || print "3Couldn't look for tags in $file! $! $txt_string";
        while (<FH>) {
            if (!/^#tags/i) {
                next;
            } elsif ($. > 2) {
                last;
            } elsif (/\b$tag/i) {
                push (@tag_files, $file);
                last;
            }
        }
        close (FH);
    }
    &print_page (@tag_files);

#get comments
}elsif (($query =~ /^\w+\.post\s[\w[:punct:]]+/) && (length($query) < 950)) {
    my $comment = $query;
    my @s_comment= (split (/ /,$comment));
    my $post;
    if ($s_comment[0] =~ /\w+\.post/) {
        $post = $s_comment[0];
    }
    my $comfile = "$dir/$post.cmt";
    my $tmp = "$comfile.tmp";
    my $go_string = "\t$base_dir/$name?$post\t$server\t$port";

    if (-e "$dir/$post") {
        open(NEW, "> $tmp");
        flock(NEW, LOCK_EX);
        my $date = strftime ("%Y %B %d, %R", localtime((stat ($tmp))[9]));
        print NEW "$date\n";
        print NEW wrap ("", "", @s_comment[1..$#s_comment]), "\n";
        print NEW "\n$cmt_div\n\n";
        if (-e $comfile) {
            open (OLD, "< $comfile");
            flock (OLD, LOCK_EX);
            while (my $line = <OLD>) {
                print NEW $line;
            }  
            close OLD;
        }
        close NEW;
        rename ($tmp, $comfile) || die "Can't rename $comfile!";
        chmod 0640, $comfile;
        print "iYour comment has been posted.$txt_string\r\n";
        print "1View your comment$go_string\r\n";
    } else {
        print "3Sorry, $post does not exist.\t$txt_string\r\n";
        print "1Back to Main Page$com_string\r\n";
    }
} elsif (($query =~ /\w+\.post\s[\w[:punct:]]+/) && (length($query) > 950)) {
    print "3Sorry, comment should be less than 950 characters.$txt_string\r\n";
    print "1Back to Main Page$com_string\r\n";

#print error page
} elsif (($query !~ /\w+\.post\s[\w[:punct:]]/) && ($query !~ /archive\d/) && (length($query) > 0)) {
    print "3Oh shoot, something's gone wrong.$txt_string\r\n";
    print "1Back to Main Page$com_string\r\n";
}
print $footer;

#Here there be subroutines

#print individual posts as well as header and div files 
sub print_file {
    my $file = "$dir/$_[0]";
    if (-s $file) {
        open (FH, "< $file") || print "3Can't Open $file! $! $txt_string\r\n";
        if ($file =~ /txt$/) {
            while (<FH>) {
                chomp; 
                print "i$_$txt_string\r\n";
            }
        } else {
            @tag_list = "";
            while (<FH>) {
                chomp;    
                if ($_ =~ s/^#tags\s+//i) {
                    @tag_list = split (/\s*,\s*/, $_);
                } elsif ( $_ =~ /^[0-9ceghisIMT].+?\t/ ) {
                    print "$_\r\n";
                } elsif ($_ =~ /^--more--$/)  {
                    if ($query =~ /^\w+\.post$/) {
                        next;
                    } else {
                        print "i$more_text$txt_string\r\n";
                        last;
                    }
                } else {
                    print "i$_$txt_string\r\n";
                } 
            } 
         }
         close (FH);
     }
}

#print pages of posts (main page and archive pages).  Counts comments as well.
sub print_page {
    my @print_list = @_;
    &print_file ($header);
    &print_file ($div);
    foreach my $file (@print_list) {
        my $cmt_count = 0;
        my @p_name = split /\//, $file;
        my $p = 0;
        until ($p_name[$p] =~ /post$/) {
            $p++;
        }
        my $go_string = "\t$base_dir/$name?$p_name[$p]\t$server\t$port";
        my $date = strftime ("%Y %B %d, %R", localtime((stat ("$dir/$file"))[9]));
        
        print "i$date$txt_string\r\n";
        print "i$txt_string\r\n";
        &print_file ($file);
        if (-e "$dir/$file.cmt") {
            open (FH, "< $dir/$file.cmt") || print "3Can't count comments for $file! $! $txt_string\r\n";
            while (<FH>) {
                chomp;
                if ($_ =~ /$cmt_div/) {   
                    $cmt_count += 1;
                }
            }
            close (FH);
        }
        print "1$permalink_text($cmt_count)$go_string\r\n";
        if ($tag_list[0]) {
            &print_tags (@tag_list);
        }
        &print_file ($div);
    }
}

#print tag list
sub print_tags {
    my @tags = @_;
    print "i$cmt_div$txt_string\r\n";
    print "iTags:$txt_string\r\n";
    foreach my $tag (@tags) {
        my $tag_link = $tag;
        $tag_link =~ s/\s+/_/g;
        print "1$tag\t$base_dir/$name?tag=$tag_link\t$server\t$port\r\n";
    }
}

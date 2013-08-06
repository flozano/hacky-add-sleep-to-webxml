import logging
from fabric.decorators import task
from fabric.operations import *
from fabric.contrib import *
from xml.sax.saxutils import escape
logging.basicConfig(level=logging.INFO)

DEFAULT_APP='ufe'
DEFAULT_INSTANCE='0'


def _web_xml(app=DEFAULT_APP, instance=DEFAULT_INSTANCE):
	return "/opt/%s/instances/%s/conf/web.xml" % (app, instance)

def _prefix(name, pattern, min_sleep, max_sleep):
	return "<!--sleep:name=%s,pattern=%s,min-sleep=%s,max-sleep=%s-->" % (name, escape(pattern), min_sleep, max_sleep)

def _sed_escape(text):
    for char in "/'().*":
        text = text.replace(char, r'\%s' % char)
    return text

def build_filter():
	local("mvn clean package")

def upload_filter(remote_path):
	files=put(local_path="./target/add-sleep-to-request*.jar", remote_path=remote_path, use_sudo=True, mode="644")
	# TODO ensure only one JAR is built
	return files[0]

def build_content(name, pattern, min_sleep, max_sleep):
	return "<filter><filter-name>%s</filter-name><filter-class>com.kii.common.SleepFilter</filter-class><init-param><param-name>pattern</param-name><param-value>%s</param-value></init-param><init-param><param-name>min-sleep</param-name><param-value>%s</param-value></init-param><init-param><param-name>max-sleep</param-name><param-value>%s</param-value></init-param></filter><filter-mapping><filter-name>%s</filter-name><url-pattern>/*</url-pattern></filter-mapping><!-- keep this in a single line for automation -->" % (name, pattern, min_sleep, max_sleep, name )

def add_line_to_file(prefix, line,file,marker = "  <!-- ==================== Built In Filter Mappings ====================== -->"):
	line_with_prefix = prefix+line
	logging.info("Adding %s to %s after %s" % (line_with_prefix, file, marker))
	#### REALLY HACKY
	sudo("sed -i.bak -r -e '/%s/ a\%s' \"$(echo %s)\"" % (_sed_escape(marker), _sed_escape(line_with_prefix), file))

def remove_line_from_file(contains, file):
	logging.info("Removing %s from %s " % (contains, file))
	sudo("sed -i.bak -r -e '/%s/d' \"$(echo %s)\"" % (_sed_escape(contains), file))

@task
def add_sleep(name, pattern, min_sleep, max_sleep, app=DEFAULT_APP, instance=DEFAULT_INSTANCE):
	"""
	Add a new sleep to requests with a given pattern.

	Parameters:
	-----------
	name: name of the 'sleep' filter, for identification purposes
	pattern: java regexp pattern that will be used to match against the requests. SHELL-ESCAPE!
	min_sleep: the minimum amount of time to use in the Thread.sleep() before the request, in msecs
	max_sleep: the maximum amount of time to use in the Thread.sleep() before the request, in msecs
	app: app name. Optional.
	instance: instance ID. Optional, defaults to 0.
	"""
	build_filter()
	jar_file = upload_filter(remote_path="/opt/%s/instances/%s/lib" % (app, instance))
	line = build_content(name, pattern, min_sleep, max_sleep)
	prefix = _prefix(name, pattern, min_sleep, max_sleep)
	web_xml_file = _web_xml(app, instance)
	add_line_to_file(prefix, line, web_xml_file)

@task
def list_sleeps(app=DEFAULT_APP, instance=DEFAULT_INSTANCE):
	"""
	list sleep filter lines

	Parameters:
	-----------
	app: app name. Optional.
	instance: instance ID. Optional, defaults to 0.
	"""
	web_xml_file = _web_xml(app, instance)
	sudo("grep \"%s\" \"%s\" " % ("sleep", web_xml_file ))


@task
def remove_sleep(name, pattern, min_sleep, max_sleep, app=DEFAULT_APP, instance=DEFAULT_INSTANCE):
	"""
	Remove an existing sleep


	Parameters:
	-----------
	name, pattern, min_sleep, max_sleep, app and instance:
	    same as used in add_sleep, or same as listed in list_sleep
	"""
	web_xml_file = _web_xml(app, instance)
	prefix = _prefix(name, pattern, min_sleep, max_sleep)
	web_xml_file = _web_xml(app, instance)
	remove_line_from_file(prefix, web_xml_file)

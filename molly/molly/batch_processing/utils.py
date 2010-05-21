import simplejson, os.path, sys

from molly.conf import all_apps

from molly.conf import app_by_local_name
from molly.batch_processing.models import Batch


def load_batches():
    batch_details = []
    for app in all_apps():
        for provider in app.providers:
            for method_name in dir(provider):
                method = getattr(provider, method_name)
                if not getattr(method, 'is_batch', False):
                    continue
                print dir(provider.__class__)
                    
                batch_details.append({
                    'title': method.__doc__ or provider.class_path,
                    'local_name': app.local_name,
                    'provider_name': provider.class_path,
                    'method_name': method_name,
                    'cron_stmt': method.cron_stmt,
                    'initial_metadata': method.initial_metadata,
                })

    batches = set()
    for batch_detail in batch_details:
        batch, _ = Batch.objects.get_or_create(
            local_name = batch_detail['local_name'],
            provider_name = batch_detail['provider_name'],
            method_name = batch_detail['method_name'],
            defaults = {'title': batch_detail['title'],
                        'cron_stmt': batch_detail['cron_stmt'],
                        '_metadata': simplejson.dumps(batch_detail['initial_metadata'])})
        batches.add(batch)
    for batch in Batch.objects.all():
        if not batch in batches:
            batch.delete()

def run_batch(local_name, provider_name, method_name):
    
    batch = Batch.objects.get(
        local_name=local_name,
        provider_name=provider_name,
        method_name=method_name)
        
    batch.run(True)

    return batch.log

def _escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

def create_crontab(filename):
    load_batches()

    f = open(filename, 'w') if isinstance(filename, basestring) else filename
    f.write("# Generated by Molly. Do not edit by hand, or else your changes\n")
    f.write("# will be overwritten.\n\n")
    f.write('MAILTO=""\n')
    f.write("DJANGO_SETTINGS_MODULE=%s\n\n" % os.environ['DJANGO_SETTINGS_MODULE'])

    for batch in Batch.objects.all():
        if not batch.enabled:
            continue
        f.write('%s %s "%s" "%s" "%s"\n' % (
            batch.cron_stmt.ljust(20),
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts', 'run_batch.py')),
            _escape(batch.local_name),
            _escape(batch.provider_name),
            _escape(batch.method_name),
        ))

    
if __name__ == '__main__':
    create_crontab(sys.stdout)
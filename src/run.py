"""Produce and immediately replay one exact finite certificate."""
import argparse,json,os,resource,sys,time
from pathlib import Path
from exact import certificate
from verify import read_json,replay,Invalid


def bound_process():
    # Linux reference runner; one worker, no GPU, no subprocesses in this command.
    if hasattr(os,'sched_getaffinity'):
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(3500*1024**2,3500*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--source',action='store_true',help='project a finite Boolean source model first')
    args=parser.parse_args();bound_process()
    start=time.process_time();wall=time.perf_counter()
    try:
        task=read_json(args.input);scope=None
        if args.source:
            from front_end import derive
            task,scope=derive(task)
        cert=certificate(task);value=replay(task,cert)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8')
        if scope is not None:
            args.output.with_suffix('.task.json').write_text(json.dumps(task,indent=2)+'\n',encoding='utf-8')
            args.output.with_suffix('.scope.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'loss':str(value),'cpu_seconds':time.process_time()-start,
                          'wall_seconds':time.perf_counter()-wall,
                          'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          'workers':1},sort_keys=True))
        return 0
    except (Invalid,ValueError,ArithmeticError,OSError,TypeError,KeyError,IndexError) as e:
        print(f'FAILED: {e}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())

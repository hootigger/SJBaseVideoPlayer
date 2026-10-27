"""Run the actual queued-play implementation against a deterministic scheduler."""
from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
src = (root / 'SJBaseVideoPlayer/SJBaseVideoPlayer.m').read_text()
start = src.index('    NSUInteger request = ++_audioSessionPlaybackRequest;')
end = src.index('\n}\n\n- (void)pause {', start)
body = src[start:end]
for method in ['pause', 'stop', 'replay']:
    start_method = src.index(f'- (void){method} {{\n')
    assert '++_audioSessionPlaybackRequest;' in src[start_method:src.index('\n}', start_method)]
stub = r'''
#import <Foundation/Foundation.h>
#import <assert.h>
typedef NSString *AVAudioSessionCategory;
typedef NSUInteger AVAudioSessionCategoryOptions;
typedef NSUInteger AVAudioSessionSetActiveOptions;
static NSMutableArray *backgroundTasks, *mainTasks;
static int SJAudioSessionQueue(void) { return 1; }
#define dispatch_get_main_queue() 2
#define dispatch_async(queue, block) [(queue == 1 ? backgroundTasks : mainTasks) addObject:[block copy]]
static void drain(NSMutableArray *tasks) { while (tasks.count) { void (^b)(void) = tasks.firstObject; [tasks removeObjectAtIndex:0]; b(); } }
@interface AVAudioSession : NSObject
+ (instancetype)sharedInstance;
- (BOOL)setCategory:(NSString*)c withOptions:(NSUInteger)o error:(NSError**)e;
- (BOOL)setActive:(BOOL)a withOptions:(NSUInteger)o error:(NSError**)e;
@end
@implementation AVAudioSession
+ (instancetype)sharedInstance { static id s; if (!s) s=[self new]; return s; }
- (BOOL)setCategory:(NSString*)c withOptions:(NSUInteger)o error:(NSError**)e { return YES; }
- (BOOL)setActive:(BOOL)a withOptions:(NSUInteger)o error:(NSError**)e { return YES; }
@end
@interface Playback : NSObject
@property int count;
- (void)play;
- (void)resume;
@end
@implementation Playback
- (void)play { self.count++; }
- (void)resume {}
@end
@interface Registrar : NSObject
@property int state;
@end
@implementation Registrar
@end
static const int SJVideoPlayerAppState_Background=1;
typedef struct { struct { BOOL isEnabled; } audioSessionControl; } Control;
@interface Player : NSObject {
@public
    Control *_controlInfo;
    NSUInteger _audioSessionPlaybackRequest;
    NSString *_mCategory;
    NSUInteger _mCategoryOptions, _mSetActiveOptions;
    Playback *_playbackController;
}
@property Registrar *registrar;
@property BOOL isPausedInBackground;
@property Playback *controlLayerAppearManager;
- (void)play;
@end
@implementation Player
- (instancetype)init { if ((self=[super init])) { _controlInfo=calloc(1,sizeof(Control)); _controlInfo->audioSessionControl.isEnabled=YES; _playbackController=[Playback new]; self.registrar=[Registrar new]; self.controlLayerAppearManager=[Playback new]; } return self; }
- (void)dealloc { free(_controlInfo); }
- (void)play {
'''
checks = r'''
}
@end
int main() { @autoreleasepool {
 backgroundTasks=[NSMutableArray new]; mainTasks=[NSMutableArray new];
 Player *p=[Player new];
 [p play]; assert(p->_playbackController.count==0);
 drain(backgroundTasks); ++p->_audioSessionPlaybackRequest; drain(mainTasks);
 assert(p->_playbackController.count==0); // Pause/stop while activation is in flight.
 [p play]; [p play]; drain(backgroundTasks); drain(mainTasks);
 assert(p->_playbackController.count==1); // Only newest request starts.
 p.isPausedInBackground=YES; [p play]; p.registrar.state=1;
 drain(backgroundTasks); drain(mainTasks); assert(p->_playbackController.count==1);
 p.registrar.state=0; [p play]; drain(backgroundTasks); drain(mainTasks);
 assert(p->_playbackController.count==2);
 puts("PASS: activation precedes playback; cancellation, replacement and background are respected");
} return 0; }
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'check.m'; p.write_text((stub+body+checks).replace('AVAudioSession', 'TestAudioSession'))
 binary=Path(d)/'check'
 subprocess.run(['xcrun','clang','-fobjc-arc','-fblocks','-framework','Foundation',str(p),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)

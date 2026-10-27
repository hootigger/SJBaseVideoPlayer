"""Exercise the actual window selection helper using Foundation-backed UI stubs.

Run on macOS: python3 Tests/test_window_context.py
Rotation animations and UIKit window lifetime still require device testing.
"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
header = (root / "SJBaseVideoPlayer/Common/Implements/SJPlayerWindowContext.h").read_text()
header = header.replace("#import <UIKit/UIKit.h>", "")
stubs = r'''
#import <Foundation/Foundation.h>
#import <assert.h>
typedef NS_ENUM(NSInteger, UISceneActivationState) {
    UISceneActivationStateForegroundActive,
    UISceneActivationStateForegroundInactive,
    UISceneActivationStateBackground
};
static const double UIWindowLevelNormal = 0;
@class UIWindow, UIWindowScene;
@interface UIView : NSObject
@property(nonatomic, weak) UIWindow *window;
@end
@implementation UIView
@end
@interface UIWindow : UIView
@property(nonatomic, strong) UIWindowScene *windowScene;
@property(nonatomic, strong) NSObject *rootViewController;
@property(nonatomic) BOOL hidden;
@property(nonatomic) double windowLevel;
@end
@implementation UIWindow
@end
@interface UIScene : NSObject
@property(nonatomic) UISceneActivationState activationState;
@end
@implementation UIScene
@end
@interface UIWindowScene : UIScene
@property(nonatomic, copy) NSArray<UIWindow *> *windows;
@end
@implementation UIWindowScene
@end
@interface AppDelegate : NSObject
@property(nonatomic, strong) UIWindow *window;
@end
@implementation AppDelegate
@end
@interface UIApplication : NSObject
+ (instancetype)sharedApplication;
@property(nonatomic, copy) NSArray<UIScene *> *connectedScenes;
@property(nonatomic, strong) AppDelegate *delegate;
@property(nonatomic, strong) UIWindow *keyWindow;
@end
@implementation UIApplication
+ (instancetype)sharedApplication { static UIApplication *app; if (!app) app = [self new]; return app; }
@end
'''
checks = r'''
int main(void) { @autoreleasepool {
    UIApplication *app = UIApplication.sharedApplication;
    assert(SJPlayerWindowForView(nil) == nil);
    UIWindowScene *inactive = [UIWindowScene new];
    inactive.activationState = UISceneActivationStateForegroundInactive;
    UIWindowScene *active = [UIWindowScene new];
    active.activationState = UISceneActivationStateForegroundActive;
    UIWindow *source = [UIWindow new]; source.windowScene = inactive;
    source.rootViewController = [NSObject new];
    UIWindow *main = [UIWindow new]; main.windowScene = active;
    main.rootViewController = [NSObject new];
    UIWindow *overlay = [UIWindow new]; overlay.windowScene = active;
    overlay.windowLevel = 1000; overlay.rootViewController = [NSObject new];
    active.windows = @[overlay, main]; inactive.windows = @[source];
    app.connectedScenes = @[inactive, active]; app.keyWindow = overlay;
    UIView *view = [UIView new]; view.window = source;
    assert(SJPlayerWindowForView(view) == source); // Source wins over another active Scene.
    assert(SJPlayerWindowForView(source) == source);
    assert(SJPlayerWindowForView(nil) == main); // Overlay is not a business fallback.
    app.delegate = [AppDelegate new]; app.delegate.window = main;
    assert(SJPlayerWindowForView(nil) == main);
    app.connectedScenes = @[inactive];
    assert(SJPlayerWindowForView(nil) == source);
    inactive.activationState = UISceneActivationStateBackground;
    assert(SJPlayerWindowForView(nil) == nil);
    puts("PASS: player uses source window, rejects foreign Scene/overlays and handles inactive/no Scene");
} return 0; }
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "check.m"
    path.write_text(stubs + header + checks)
    binary = Path(directory) / "check"
    subprocess.run(["xcrun", "clang", "-fobjc-arc", "-framework", "Foundation", str(path), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

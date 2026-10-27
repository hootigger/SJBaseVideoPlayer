#import <UIKit/UIKit.h>

// Keep player UI in its source window; never select a key window from another Scene.
static inline UIWindow * _Nullable SJPlayerWindowForView(UIView * _Nullable view) {
    UIWindow *source = [view isKindOfClass:UIWindow.class] ? (UIWindow *)view : view.window;
    if (source != nil) return source;
    UIApplication *app = UIApplication.sharedApplication;
    if (@available(iOS 13.0, *)) {
        UIWindowScene *scene = nil;
        for (NSNumber *state in @[@(UISceneActivationStateForegroundActive), @(UISceneActivationStateForegroundInactive)]) {
            for (UIScene *candidate in app.connectedScenes) {
                if ([candidate isKindOfClass:UIWindowScene.class] && candidate.activationState == state.integerValue) {
                    scene = (UIWindowScene *)candidate;
                    break;
                }
            }
            if (scene != nil) break;
        }
        if (scene == nil) return nil;
        UIWindow *main = [app.delegate respondsToSelector:@selector(window)] ? app.delegate.window : nil;
        if (main.windowScene == scene && main != nil) return main;
        for (UIWindow *window in scene.windows) {
            if (!window.hidden && window.windowLevel == UIWindowLevelNormal && window.rootViewController != nil) return window;
        }
        return nil;
    }
    return app.keyWindow;
}

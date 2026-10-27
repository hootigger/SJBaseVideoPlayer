# Legacy IJKPlayer specification

The original `SJBaseVideoPlayer_ijkplayer.podspec` is preserved here unchanged.
It declares the same Pod name as the main specification but uses older settings.
CocoaPods scans root-level specifications when installing from Git; keeping both
at the root caused the legacy 3.7.4 specification to replace the main 3.7.8 one.
Only `SJBaseVideoPlayer.podspec` should be discovered automatically.

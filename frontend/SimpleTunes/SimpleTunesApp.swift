import SwiftUI

@main
struct SimpleTunesApp: App {
    @StateObject private var player = PlayerViewModel()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(player)
        }
    }
}

import SwiftUI

struct QueuePanel: View {
    @EnvironmentObject var player: PlayerViewModel
    @Binding var isVisible: Bool
    
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("Up Next").font(.headline)
                Spacer()
                Button("Clear") { player.clearQueue() }.disabled(player.queue.isEmpty)
                Button { isVisible = false } label: {
                    Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                }.buttonStyle(.plain)
            }.padding().background(.bar)
            
            Divider()
            
            if player.queue.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "list.bullet").font(.largeTitle).foregroundStyle(.secondary)
                    Text("Queue is empty").foregroundStyle(.secondary)
                }
                Spacer()
            } else {
                if let current = player.currentTrack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("NOW PLAYING").font(.caption2).foregroundStyle(.secondary)
                        QueueTrackRow(track: current, isPlaying: true, position: nil)
                    }.padding(.horizontal).padding(.vertical, 8).background(.accent.opacity(0.1))
                }
                
                List {
                    Section {
                        ForEach(Array(upcomingTracks.enumerated()), id: \.element.id) { index, track in
                            QueueTrackRow(track: track, isPlaying: false, position: index + 1)
                                .contentShape(Rectangle())
                                .onTapGesture { playFromQueue(index: player.queueIndex + index + 1) }
                                .swipeActions(edge: .trailing) {
                                    Button(role: .destructive) {
                                        player.removeFromQueue(at: player.queueIndex + index + 1)
                                    } label: { Label("Remove", systemImage: "trash") }
                                }
                        }.onMove(perform: moveInQueue)
                    } header: {
                        if !upcomingTracks.isEmpty { Text("NEXT UP • \(upcomingTracks.count) tracks") }
                    }
                }.listStyle(.plain)
            }
        }
        .frame(width: 320)
        .background(.ultraThinMaterial)
    }
    
    private var upcomingTracks: [Track] {
        guard player.queueIndex + 1 < player.queue.count else { return [] }
        return Array(player.queue[(player.queueIndex + 1)...])
    }
    
    private func playFromQueue(index: Int) {
        guard player.queue.indices.contains(index) else { return }
        player.queueIndex = index; player.play(track: player.queue[index])
    }
    
    private func moveInQueue(from source: IndexSet, to destination: Int) {
        let offset = player.queueIndex + 1
        player.queue.move(fromOffsets: IndexSet(source.map { $0 + offset }), toOffset: destination + offset)
    }
}

struct QueueTrackRow: View {
    let track: Track, isPlaying: Bool
    let position: Int?
    
    var body: some View {
        HStack(spacing: 10) {
            if let pos = position {
                Text("\(pos)").font(.caption).foregroundStyle(.secondary).frame(width: 20)
            } else if isPlaying {
                Image(systemName: "speaker.wave.2.fill").font(.caption).foregroundStyle(.accent).frame(width: 20)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(track.title).fontWeight(isPlaying ? .semibold : .regular)
                    .foregroundStyle(isPlaying ? .accent : .primary).lineLimit(1)
                Text(track.artist).font(.caption).foregroundStyle(.secondary).lineLimit(1)
            }
            Spacer()
            Text(track.durationFormatted).font(.caption).foregroundStyle(.secondary)
        }.padding(.vertical, 4)
    }
}

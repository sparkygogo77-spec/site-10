package com.sparky.lanternring.client;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * Removes the old Lantern Ring jar after an update. Windows keeps a running game's jars locked, so
 * {@link #removeAfterExit} starts a small separate Java process (this class's {@link #main}, run from
 * the new jar) that waits for the game to close and then deletes the old jar. That way the next start
 * sees only the new one. Uses nothing from Minecraft, so it runs on a bare JVM.
 */
public final class JarSwap {
	private JarSwap() {
	}

	static void removeAfterExit(Path oldJar, Path newJar) {
		try {
			boolean windows = System.getProperty("os.name", "").toLowerCase().contains("win");
			Path bin = Path.of(System.getProperty("java.home"), "bin");
			Path java = bin.resolve(windows ? "javaw.exe" : "java");
			if (!Files.exists(java)) java = bin.resolve(windows ? "java.exe" : "java");
			new ProcessBuilder(List.of(java.toString(), "-cp", newJar.toString(), JarSwap.class.getName(),
					Long.toString(ProcessHandle.current().pid()), oldJar.toString()))
					.redirectOutput(ProcessBuilder.Redirect.DISCARD)
					.redirectError(ProcessBuilder.Redirect.DISCARD)
					.start();
		} catch (Exception e) {
			// The next start deletes it instead (RingUpdater.init) if the game gets that far.
		}
	}

	/** Args: the game's process id, then the jar to delete once it has exited. */
	public static void main(String[] args) throws InterruptedException {
		if (args.length < 2) return;
		try {
			ProcessHandle.of(Long.parseLong(args[0])).ifPresent(game -> game.onExit().join());
		} catch (RuntimeException ignored) {
			// Can't watch the game; just keep trying to delete below.
		}
		Path old = Path.of(args[1]);
		// Windows can hold the file a moment after the process ends; keep trying for a few minutes.
		for (int i = 0; i < 360; i++) {
			try {
				Files.deleteIfExists(old);
				return;
			} catch (Exception e) {
				Thread.sleep(500);
			}
		}
	}
}

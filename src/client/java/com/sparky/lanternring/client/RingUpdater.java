package com.sparky.lanternring.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternRing;
import java.io.IOException;
import java.io.InputStream;
import java.io.Reader;
import java.io.Writer;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.ZipFile;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;

/**
 * In-game updater: asks the private repo's `builds` branch (latest.json next to lantern-ring-latest.jar)
 * whether a newer jar is out, says so in chat, and on request downloads it next to the running jar.
 * The old jar is removed once the game has closed (see {@link JarSwap}), so the new one loads on restart.
 * Needs a read-only GitHub token, saved in config/lanternring-updater.json. Without a token or network
 * it does nothing. The token is never logged or shown in chat.
 */
public final class RingUpdater {
	private static final String API = "https://api.github.com/repos/sparkygogo77-spec/site-10/contents/";
	private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("lanternring-updater.json");
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	/** Re-check this often while playing. */
	private static final long RECHECK_MS = 10 * 60 * 1000L;

	public enum State { IDLE, CHECKING, UP_TO_DATE, AVAILABLE, DOWNLOADING, READY, FAILED }

	/** What's saved on disk. */
	private static final class Config {
		String token = "";
		/** Jars this updater replaced; deleted on start if they're still there and not the running jar. */
		List<String> pendingDelete = new ArrayList<>();
	}

	private static Config config;
	private static HttpClient http;
	private static volatile State state = State.IDLE;
	private static volatile String latestVersion = "";
	private static volatile String latestNote = "";
	private static volatile String message = "";
	private static volatile String announced = "";
	private static volatile long lastCheck;

	private RingUpdater() {
	}

	public static State state() {
		return state;
	}

	public static String latestVersion() {
		return latestVersion;
	}

	/** A short line for the Updates screen. */
	public static String message() {
		return message;
	}

	public static boolean hasToken() {
		return !config().token.isBlank();
	}

	/** The saved token, for other Ring Lab pages that talk to GitHub (see {@link RingInbox}). */
	static String token() {
		return config().token;
	}

	public static void setToken(String token) {
		config().token = token == null ? "" : token.trim();
		save();
	}

	/** Called once when the client starts: finish removing a jar an earlier update replaced. */
	public static void init() {
		Config c = config();
		if (c.pendingDelete.isEmpty()) return;
		Path running = runningJar();
		c.pendingDelete.removeIf(p -> {
			Path old = Path.of(p);
			if (old.equals(running)) return false;
			try {
				Files.deleteIfExists(old);
				return true;
			} catch (IOException | RuntimeException e) {
				return false;
			}
		});
		save();
	}

	/** Check on joining a world, and again every few minutes while playing. */
	public static void tick(Minecraft client) {
		if (client.player == null || state == State.CHECKING || state == State.DOWNLOADING || state == State.READY) return;
		if (System.currentTimeMillis() - lastCheck > RECHECK_MS) check();
	}

	public static void onJoin() {
		if (state == State.AVAILABLE) announce(true);
		else if (state != State.READY) lastCheck = 0;
	}

	/** Asks the repo for the newest version, off the game thread. Quiet when there's no token or network. */
	public static void check() {
		lastCheck = System.currentTimeMillis();
		String token = config().token;
		if (token.isBlank()) {
			message = "Paste a GitHub token to turn on updates.";
			return;
		}
		if (state == State.CHECKING || state == State.DOWNLOADING || state == State.READY) return;
		state = State.CHECKING;
		message = "Checking...";
		HttpRequest request = request(token, "latest.json").timeout(Duration.ofSeconds(15)).build();
		client().sendAsync(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8)).whenComplete((response, error) -> {
			if (error != null) {
				fail("Couldn't reach GitHub.");
				return;
			}
			if (response.statusCode() == 401 || response.statusCode() == 403) {
				fail("GitHub refused the token (" + response.statusCode() + ").");
				return;
			}
			if (response.statusCode() != 200) {
				fail("No version info on GitHub yet (" + response.statusCode() + ").");
				return;
			}
			try {
				JsonObject json = JsonParser.parseString(response.body()).getAsJsonObject();
				latestVersion = json.get("version").getAsString();
				latestNote = json.has("note") ? json.get("note").getAsString() : "";
			} catch (RuntimeException e) {
				fail("Couldn't read the version info.");
				return;
			}
			if (compare(latestVersion, LanternRing.version()) > 0) {
				state = State.AVAILABLE;
				message = latestVersion + " is out" + (latestNote.isEmpty() ? "." : ": " + latestNote);
				Minecraft.getInstance().execute(() -> announce(false));
			} else {
				state = State.UP_TO_DATE;
				message = "You have the newest version.";
			}
		});
	}

	/** Downloads the newest jar next to the running one and lines up the old one for removal. */
	public static void download() {
		if (state != State.AVAILABLE) {
			if (!message.isEmpty()) chat(Component.literal("[Lantern Ring] " + message).withStyle(ChatFormatting.GRAY));
			return;
		}
		Path running = runningJar();
		Path modsDir = running != null ? running.getParent() : FabricLoader.getInstance().getGameDir().resolve("mods");
		String version = latestVersion;
		Path target = modsDir.resolve("lantern-ring-" + version + ".jar");
		Path part = modsDir.resolve(target.getFileName() + ".part");
		state = State.DOWNLOADING;
		message = "Downloading " + version + "...";
		chat(Component.literal(message).withStyle(ChatFormatting.GRAY));
		HttpRequest request = request(config().token, "lantern-ring-latest.jar").timeout(Duration.ofMinutes(5)).build();
		client().sendAsync(request, HttpResponse.BodyHandlers.ofFile(part)).whenComplete((response, error) -> {
			try {
				if (error != null || response.statusCode() != 200) {
					throw new IOException("download failed");
				}
				// Only keep it if it really is a Lantern Ring jar of the version we announced.
				String got = jarVersion(part);
				if (got == null || compare(got, LanternRing.version()) <= 0) throw new IOException("not a newer Lantern Ring jar");
				Files.move(part, target, StandardCopyOption.REPLACE_EXISTING);
				latestVersion = got;
				if (running != null && !running.equals(target)) {
					Config c = config();
					if (!c.pendingDelete.contains(running.toString())) c.pendingDelete.add(running.toString());
					save();
					JarSwap.removeAfterExit(running, target);
				}
				state = State.READY;
				message = got + " downloaded. Restart Minecraft to use it.";
				Minecraft.getInstance().execute(() -> chat(Component.literal("[Lantern Ring] ").withStyle(ChatFormatting.GREEN)
						.append(Component.literal(message).withStyle(ChatFormatting.WHITE))));
			} catch (IOException | RuntimeException e) {
				try {
					Files.deleteIfExists(part);
				} catch (IOException ignored) {
					// Nothing more to clean up.
				}
				state = State.AVAILABLE;
				message = "Download failed. Try again from Ring Lab > Updates.";
				Minecraft.getInstance().execute(() -> chat(Component.literal("[Lantern Ring] " + message).withStyle(ChatFormatting.RED)));
			}
		});
	}

	private static void announce(boolean again) {
		if (state != State.AVAILABLE || (!again && latestVersion.equals(announced))) return;
		if (Minecraft.getInstance().player == null) return;
		announced = latestVersion;
		Component button = Component.literal("[Click to update]").withStyle(style -> style
				.withColor(ChatFormatting.AQUA).withUnderlined(true)
				.withClickEvent(new ClickEvent.RunCommand("/lanternring update"))
				.withHoverEvent(new HoverEvent.ShowText(Component.literal("Download " + latestVersion + " into your mods folder"))));
		chat(Component.literal("[Lantern Ring] ").withStyle(ChatFormatting.GREEN)
				.append(Component.literal(message + " ").withStyle(ChatFormatting.WHITE))
				.append(button));
	}

	private static void chat(Component text) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player != null) mc.gui.chatListener().handleSystemMessage(text, false);
	}

	private static void fail(String why) {
		state = State.FAILED;
		message = why;
	}

	private static HttpRequest.Builder request(String token, String file) {
		return HttpRequest.newBuilder(URI.create(API + file + "?ref=builds"))
				.header("Accept", "application/vnd.github.raw+json")
				.header("Authorization", "Bearer " + token)
				.header("X-GitHub-Api-Version", "2022-11-28")
				.header("User-Agent", "lantern-ring-updater");
	}

	private static HttpClient client() {
		if (http == null) {
			http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10))
					.followRedirects(HttpClient.Redirect.NORMAL).build();
		}
		return http;
	}

	/** The version in a downloaded jar's fabric.mod.json, or null if it isn't a Lantern Ring jar. */
	private static String jarVersion(Path jar) {
		try (ZipFile zip = new ZipFile(jar.toFile())) {
			var entry = zip.getEntry("fabric.mod.json");
			if (entry == null) return null;
			try (InputStream in = zip.getInputStream(entry)) {
				JsonObject json = JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
				if (!LanternRing.MOD_ID.equals(json.get("id").getAsString())) return null;
				return json.get("version").getAsString();
			}
		} catch (IOException | RuntimeException e) {
			return null;
		}
	}

	/** The jar this game loaded Lantern Ring from, or null in a dev run (classes folder). */
	static Path runningJar() {
		return FabricLoader.getInstance().getModContainer(LanternRing.MOD_ID)
				.flatMap(mod -> mod.getOrigin().getPaths().stream().findFirst())
				.filter(p -> Files.isRegularFile(p) && p.getFileName().toString().endsWith(".jar"))
				.map(p -> p.toAbsolutePath().normalize())
				.orElse(null);
	}

	/** Compares 2.1.465+26.3 style versions by their numbers before the '+'. */
	static int compare(String a, String b) {
		String[] x = a.split("\\+")[0].split("[.-]");
		String[] y = b.split("\\+")[0].split("[.-]");
		for (int i = 0; i < Math.max(x.length, y.length); i++) {
			int c = Integer.compare(number(x, i), number(y, i));
			if (c != 0) return c;
		}
		return 0;
	}

	private static int number(String[] parts, int i) {
		if (i >= parts.length) return 0;
		try {
			return Integer.parseInt(parts[i]);
		} catch (NumberFormatException e) {
			return 0;
		}
	}

	private static Config config() {
		if (config == null) {
			config = new Config();
			if (Files.exists(CONFIG)) {
				try (Reader reader = Files.newBufferedReader(CONFIG)) {
					Config loaded = GSON.fromJson(reader, Config.class);
					if (loaded != null) config = loaded;
				} catch (IOException | RuntimeException e) {
					LanternRing.LOGGER.warn("Couldn't read {}", CONFIG.getFileName());
				}
			}
			if (config.token == null) config.token = "";
			if (config.pendingDelete == null) config.pendingDelete = new ArrayList<>();
		}
		return config;
	}

	private static synchronized void save() {
		try {
			Files.createDirectories(CONFIG.getParent());
			try (Writer writer = Files.newBufferedWriter(CONFIG)) {
				GSON.toJson(config(), writer);
			}
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't save {}", CONFIG.getFileName());
		}
	}
}

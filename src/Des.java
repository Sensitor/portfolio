import java.util.Random;

public final class Des {
    private static final Random random = new Random();

    private Des() {}

    public static int lancer(int nbFaces) {
        return random.nextInt(nbFaces) + 1;
    }

    public static int lancer3d6() {
        return lancer(6) + lancer(6) + lancer(6);
    }
}
